"""Dependency-free BM25 evaluation on invented, synthetic research documents.

This is a retrieval-only educational fixture. It does NOT run an LLM, accept
patient data, validate medical advice, or establish clinical model performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
_ALLOWED_PARTITIONS = {"development", "holdout"}


class RetrievalContractError(ValueError):
    """A fixture, split, or retrieval-evaluation contract was violated."""


@dataclass(frozen=True)
class Document:
    document_id: str
    source_family_id: str
    text: str


@dataclass(frozen=True)
class Question:
    question_id: str
    source_family_id: str
    text: str
    relevant_document_ids: tuple[str, ...]
    partition: str


@dataclass(frozen=True)
class Hit:
    document_id: str
    source_family_id: str
    score: float


def tokenize(value: str) -> list[str]:
    """Document the intentionally simple, non-biomedical-specific tokenization."""
    return _TOKEN_PATTERN.findall(value.casefold())


def validate_fixture(documents: list[Document], questions: list[Question]) -> None:
    """Require fixed relevance labels and source-family-disjoint questions."""
    if not documents or not questions:
        raise RetrievalContractError("Documents and questions must be nonempty.")
    document_by_id: dict[str, Document] = {}
    for document in documents:
        if (
            not document.document_id.strip()
            or not document.source_family_id.strip()
            or not tokenize(document.text)
        ):
            raise RetrievalContractError("Blank document identifier, family, or content.")
        if document.document_id in document_by_id:
            raise RetrievalContractError("Duplicate document identifier.")
        document_by_id[document.document_id] = document

    question_ids: set[str] = set()
    families: dict[str, set[str]] = {part: set() for part in _ALLOWED_PARTITIONS}
    for question in questions:
        if (
            not question.question_id.strip()
            or not question.source_family_id.strip()
            or not tokenize(question.text)
        ):
            raise RetrievalContractError("Blank question identifier, family, or text.")
        if question.partition not in _ALLOWED_PARTITIONS:
            raise RetrievalContractError("Unrecognized question partition.")
        if question.question_id in question_ids:
            raise RetrievalContractError("Duplicate question identifier.")
        question_ids.add(question.question_id)
        families[question.partition].add(question.source_family_id)
        if len(question.relevant_document_ids) != len(set(question.relevant_document_ids)):
            raise RetrievalContractError("Duplicate qrel target.")
        for document_id in question.relevant_document_ids:
            relevant_document = document_by_id.get(document_id)
            if relevant_document is None:
                raise RetrievalContractError("Qrel points to an unknown document.")
            if relevant_document.source_family_id != question.source_family_id:
                raise RetrievalContractError("Qrel crosses source-family boundaries.")

    if not all(families.values()):
        raise RetrievalContractError("Both development and holdout partitions are required.")
    if families["development"] & families["holdout"]:
        raise RetrievalContractError("Development and holdout source families overlap.")


class BM25:
    """Deterministic lexical baseline; no external services, embeddings, or model calls."""

    def __init__(self, documents: list[Document], *, k1: float = 1.2, b: float = 0.75):
        if not documents or not (k1 > 0 and 0 <= b <= 1):
            raise RetrievalContractError("Invalid documents or BM25 parameters.")
        self.documents = list(documents)
        self.counts = [Counter(tokenize(d.text)) for d in documents]
        self.lengths = [sum(counts.values()) for counts in self.counts]
        self.average_length = sum(self.lengths) / len(self.lengths)
        if not self.average_length:
            raise RetrievalContractError("Empty document text.")
        self.frequency = Counter(
            token for counts in self.counts for token in counts.keys()
        )
        self.k1 = k1
        self.b = b

    def search(self, query: str, *, top_k: int) -> list[Hit]:
        if top_k < 1:
            raise RetrievalContractError("top_k must be positive.")
        query_terms = set(tokenize(query))
        scores: list[Hit] = []
        for document, counts, length in zip(
            self.documents, self.counts, self.lengths, strict=True
        ):
            score = 0.0
            for term in query_terms:
                term_frequency = counts.get(term, 0)
                if not term_frequency:
                    continue
                document_frequency = self.frequency[term]
                idf = math.log(
                    1 + (len(self.documents) - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                denominator = term_frequency + self.k1 * (
                    1 - self.b + self.b * length / self.average_length
                )
                score += idf * term_frequency * (self.k1 + 1) / denominator
            if score > 0:
                scores.append(Hit(document.document_id, document.source_family_id, score))
        return sorted(scores, key=lambda hit: (-hit.score, hit.document_id))[:top_k]


def _question_metrics(ranked_ids: list[str], relevant: set[str], top_k: int) -> dict:
    if not relevant:
        raise RetrievalContractError("Answerable question requires a nonempty qrel.")
    matched = [index for index, name in enumerate(ranked_ids[:top_k], 1) if name in relevant]
    discounted = sum(1 / math.log2(rank + 1) for rank in matched)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant), top_k) + 1))
    return {
        "hit_at_k": int(bool(matched)),
        "recall_at_k": len(matched) / len(relevant),
        "reciprocal_rank_at_k": 1 / matched[0] if matched else 0.0,
        "ndcg_at_k": discounted / ideal if ideal else 0.0,
    }


def evaluate_bm25(
    documents: list[Document], questions: list[Question], *, top_k: int = 3
) -> dict:
    """Evaluate only untouched holdout questions; no claimed language generation."""
    validate_fixture(documents, questions)
    ranker = BM25(documents)
    if top_k < 1:
        raise RetrievalContractError("top_k must be positive.")
    holdout = sorted(
        (question for question in questions if question.partition == "holdout"),
        key=lambda question: question.question_id,
    )
    metrics: list[dict] = []
    no_answer_empty: list[bool] = []
    evaluations: list[dict] = []
    for question in holdout:
        hits = ranker.search(question.text, top_k=top_k)
        ranked_ids = [hit.document_id for hit in hits]
        relevant = set(question.relevant_document_ids)
        evaluation = {
            "question_id": question.question_id,
            "source_family_id": question.source_family_id,
            "answerable": bool(relevant),
            "relevant_document_ids": sorted(relevant),
            "ranked": [
                {"rank": rank, **asdict(hit)}
                for rank, hit in enumerate(hits, 1)
            ],
        }
        if relevant:
            scores = _question_metrics(ranked_ids, relevant, top_k)
            metrics.append(scores)
            evaluation["retrieval_metrics"] = scores
        else:
            empty_result = not hits
            no_answer_empty.append(empty_result)
            evaluation["no_answer_empty_retrieval"] = empty_result
        evaluations.append(evaluation)

    definition = {
        "documents": [asdict(doc) for doc in documents],
        "questions": [asdict(question) for question in questions],
        "algorithm": "BM25 k1=1.2 b=0.75 lowercase alnum+underscore tokenizer",
    }
    fixture_hash = hashlib.sha256(
        json.dumps(definition, sort_keys=True).encode("utf-8")
    ).hexdigest()
    score_names = ("hit_at_k", "recall_at_k", "reciprocal_rank_at_k", "ndcg_at_k")
    aggregate = {
        key: sum(item[key] for item in metrics) / len(metrics) if metrics else None
        for key in score_names
    }
    aggregate["no_answer_empty_retrieval_rate"] = (
        sum(no_answer_empty) / len(no_answer_empty) if no_answer_empty else None
    )
    return {
        "status": "SYNTHETIC_RETRIEVAL_ONLY",
        "scientific_release_status": "BLOCKED",
        "generator_used": False,
        "model_deployment": False,
        "clinical_validation": False,
        "algorithm": definition["algorithm"],
        "fixture_sha256": fixture_hash,
        "top_k": top_k,
        "development_question_count": sum(
            question.partition == "development" for question in questions
        ),
        "holdout_question_count": len(holdout),
        "answerable_holdout_count": len(metrics),
        "unanswerable_holdout_count": len(no_answer_empty),
        "metrics": aggregate,
        "holdout_evaluations": evaluations,
    }


def make_synthetic_fixture() -> tuple[list[Document], list[Question]]:
    """Invented prose and labels; not excerpts from actual studies or patient records."""
    documents = [
        Document(
            "DOC-01", "DEV-LINK",
            "Invented cohort linkage joins participants by stable subject identifiers and visit keys.",
        ),
        Document(
            "DOC-02", "DEV-QC",
            "Invented specimen quality checks identify duplicate barcodes and missing metadata.",
        ),
        Document(
            "DOC-03", "TEST-RNA",
            "Invented RNA sequencing count analysis documents library size normalization "
            "dispersion and sample level design.",
        ),
        Document(
            "DOC-04", "TEST-SURVEY",
            "Invented population survey weighting documents strata primary sampling units "
            "and questionnaire eligibility.",
        ),
        Document(
            "DOC-05", "TEST-IMAGE",
            "Invented biomedical image geometry records voxel spacing orientation "
            "and coordinate alignment.",
        ),
    ]
    questions = [
        Question("Q-DEV1", "DEV-LINK", "How do subject visit keys join a cohort?", ("DOC-01",), "development"),
        Question("Q-DEV2", "DEV-QC", "Which checks flag duplicate barcodes?", ("DOC-02",), "development"),
        Question("Q-T01", "TEST-RNA", "What RNA count dispersion and normalization steps?", ("DOC-03",), "holdout"),
        Question("Q-T02", "TEST-SURVEY", "How should survey strata weighting sampling units work?", ("DOC-04",), "holdout"),
        Question("Q-T03", "TEST-IMAGE", "Which biomedical image voxel spacing orientation metadata?", ("DOC-05",), "holdout"),
        Question("Q-T04", "TEST-ABSENT", "What is the unlisted zephyr unobtanium protocol?", (), "holdout"),
    ]
    return documents, questions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a reproducible synthetic-only BM25 retrieval baseline"
    )
    parser.add_argument("--out", type=Path, default=Path("artifacts/rag/retrieval.json"))
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args(argv)
    documents, questions = make_synthetic_fixture()
    try:
        report = evaluate_bm25(documents, questions, top_k=args.top_k)
    except RetrievalContractError as error:
        parser.error(str(error))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"], "scientific_release_status": "BLOCKED",
        "report_path": str(args.out), "metrics": report["metrics"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
