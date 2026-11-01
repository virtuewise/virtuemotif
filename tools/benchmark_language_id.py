"""Repeatable lexical language-ID smoke benchmark (not an ASR/audio benchmark)."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.lyrics_engine import detect_text_language
from tools.validate_language_dataset import REVIEWED_STATUS, validate_corpus


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _confidence_calibration(predictions: list[dict[str, Any]], bins: int = 10) -> dict[str, Any]:
    """Measure top-label confidence against correctness; not class-probability calibration."""
    if not predictions:
        return {
            "method": "top_label_confidence_vs_correctness",
            "bins": bins,
            "expected_calibration_error": 0.0,
            "brier_score": 0.0,
            "bin_stats": [],
        }

    bucketed: list[list[dict[str, Any]]] = [[] for _ in range(bins)]
    brier_total = 0.0
    for item in predictions:
        confidence = max(0.0, min(1.0, float(item["confidence"])))
        bucket = min(int(confidence * bins), bins - 1)
        bucketed[bucket].append({**item, "bounded_confidence": confidence})
        brier_total += (confidence - float(bool(item["correct"]))) ** 2

    bin_stats = []
    ece = 0.0
    total = len(predictions)
    for index, items in enumerate(bucketed):
        if not items:
            continue
        mean_confidence = sum(item["bounded_confidence"] for item in items) / len(items)
        observed_accuracy = sum(bool(item["correct"]) for item in items) / len(items)
        ece += len(items) / total * abs(mean_confidence - observed_accuracy)
        bin_stats.append({
            "lower_bound": round(index / bins, 6),
            "upper_bound": round((index + 1) / bins, 6),
            "count": len(items),
            "mean_confidence": round(mean_confidence, 6),
            "observed_accuracy": round(observed_accuracy, 6),
        })
    return {
        "method": "top_label_confidence_vs_correctness",
        "bins": bins,
        "expected_calibration_error": round(ece, 6),
        "brier_score": round(brier_total / total, 6),
        "bin_stats": bin_stats,
        "warning": (
            "Diagnostic only: detector confidence values are heuristic scores, not "
            "validated probabilities. Interpret only against rights-cleared, reviewed data."
        ),
    }


def _code_switch_metrics(predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate binary code-switch detection using the reference mul label."""
    tp = sum(item["expected"] == "mul" and item["predicted"] == "mul" for item in predictions)
    fp = sum(item["expected"] != "mul" and item["predicted"] == "mul" for item in predictions)
    fn = sum(item["expected"] == "mul" and item["predicted"] != "mul" for item in predictions)
    tn = sum(item["expected"] != "mul" and item["predicted"] != "mul" for item in predictions)
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return {
        "positive_label": "mul",
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision": precision,
        "recall": recall,
        "f1": _ratio(2 * precision * recall, precision + recall),
        "support": tp + fn,
        "warning": "Binary code-switch metrics depend on reference labels and corpus coverage.",
    }


def evaluate(corpus: Any, split: str | None = None) -> dict[str, Any]:
    """Evaluate a corpus; reviewed datasets default to held-out test only.

    Smoke fixtures default to all examples because their only split is smoke.
    Pass split="all" explicitly to aggregate every split of a reviewed corpus.
    """
    errors = validate_corpus(corpus)
    if errors:
        raise ValueError("invalid language dataset: " + "; ".join(errors))
    assert isinstance(corpus, dict)
    all_examples = corpus["examples"]
    available_splits = sorted({example["split"] for example in all_examples})
    if split is None:
        selected_split = "test" if corpus["status"] == REVIEWED_STATUS else "all"
    else:
        selected_split = split
    if selected_split == "all":
        examples = all_examples
    else:
        examples = [example for example in all_examples if example["split"] == selected_split]
        if not examples:
            raise ValueError(
                f"requested split {selected_split!r} has no examples; "
                f"available splits: {available_splits}"
            )

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    predictions = []
    for example in examples:
        predicted = detect_text_language(example["text"])
        actual = str(predicted["language"])
        expected = example["language"]
        counts[expected]["total"] += 1
        counts[expected]["correct"] += int(actual == expected)
        confusion[expected][actual] += 1
        predictions.append({
            "id": example["id"],
            "split": example["split"],
            "expected": expected,
            "predicted": actual,
            "correct": actual == expected,
            "confidence": predicted["confidence"],
            "method": predicted["method"],
        })

    total = len(predictions)
    correct = sum(item["correct"] for item in predictions)
    cohort_languages = ("sn", "nd", "zu", "en", "mul")
    cohort_coverage = {}
    for language in cohort_languages:
        cohort_items = [item for item in predictions if item["expected"] == language]
        cohort_correct = sum(item["correct"] for item in cohort_items)
        cohort_coverage[language] = {
            "support": len(cohort_items),
            "correct": cohort_correct,
            "accuracy": _ratio(cohort_correct, len(cohort_items)),
            "represented": bool(cohort_items),
            "note": (
                "Metrics are descriptive only; empty cohorts are not evidence of zero accuracy."
                if not cohort_items else
                "Interpret only within this dataset, split, source mix, and review scope."
            ),
        }
    labels = sorted(set(corpus["labels"]) | {item["predicted"] for item in predictions})
    per_language = {}
    for language in labels:
        true_positive = sum(
            item["expected"] == language and item["predicted"] == language
            for item in predictions
        )
        false_positive = sum(
            item["expected"] != language and item["predicted"] == language
            for item in predictions
        )
        false_negative = sum(
            item["expected"] == language and item["predicted"] != language
            for item in predictions
        )
        support = sum(item["expected"] == language for item in predictions)
        precision = _ratio(true_positive, true_positive + false_positive)
        recall = _ratio(true_positive, true_positive + false_negative)
        f1 = _ratio(2 * precision * recall, precision + recall)
        per_language[language] = {
            "support": support,
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": _ratio(true_positive, support),
        }

    supported = [per_language[label] for label in sorted(counts) if counts[label]["total"]]
    macro = {
        metric: _ratio(sum(item[metric] for item in supported), len(supported))
        for metric in ("precision", "recall", "f1", "accuracy")
    }
    support_total = sum(item["support"] for item in supported)
    weighted = {
        metric: _ratio(
            sum(item[metric] * item["support"] for item in supported),
            support_total,
        )
        for metric in ("precision", "recall", "f1", "accuracy")
    }
    unknown_count = sum(item["predicted"] == "und" for item in predictions)
    expected_unknown = sum(item["expected"] == "und" for item in predictions)
    evidence_level = (
        "human_reviewed_rights_cleared"
        if corpus["status"] == REVIEWED_STATUS
        else "synthetic_smoke_only"
    )
    selected_sources = {
        example.get("source_id") for example in examples
        if isinstance(example.get("source_id"), str) and example["source_id"].strip()
    }
    selected_speakers = {
        example.get("speaker_id") for example in examples
        if isinstance(example.get("speaker_id"), str) and example["speaker_id"].strip()
    }
    governance = corpus.get("governance", {})
    evaluation_provenance = {
        "dataset_id": corpus["dataset_id"],
        "dataset_status": corpus["status"],
        "evidence_level": evidence_level,
        "evaluation_provenance": evaluation_provenance,
        "evaluated_split": selected_split,
        "evaluated_examples": total,
        "unique_source_ids_in_evaluated_split": (
            len(selected_sources) if corpus["status"] == REVIEWED_STATUS else None
        ),
        "unique_speaker_ids_in_evaluated_split": (
            len(selected_speakers) if corpus["status"] == REVIEWED_STATUS else None
        ),
        "source_split_isolation_structurally_validated": corpus["status"] == REVIEWED_STATUS,
        "declared_rights_status": governance.get("rights_status") if isinstance(governance, dict) else None,
        "declared_consent_status": governance.get("consent_status") if isinstance(governance, dict) else None,
        "declared_review_status": governance.get("review_status") if isinstance(governance, dict) else None,
        "claims_independently_verified": False,
        "warning": (
            "Metadata and split-isolation checks are structural only; they cannot prove that "
            "consent, rights clearance, native-speaker review, or speaker identities are genuine."
        ),
    }
    return {
        "schema_version": 1,
        "dataset_id": corpus["dataset_id"],
        "dataset_status": corpus["status"],
        "evidence_level": evidence_level,
        "evaluated_split": selected_split,
        "available_split_counts": {
            name: sum(example["split"] == name for example in all_examples)
            for name in available_splits
        },
        "examples": total,
        "correct": correct,
        "required_multilingual_cohorts": cohort_coverage,
        "cohort_coverage_complete": all(item["represented"] for item in cohort_coverage.values()),
        "cohort_coverage_warning": (
            "Coverage is a reporting check, not evidence of representative sampling. "
            "Missing cohorts must not be inferred accurate or inaccurate."
        ),
        "accuracy": _ratio(correct, total),
        "per_language": per_language,
        "macro_average": macro,
        "weighted_average": weighted,
        "unknown_behavior": {
            "predicted_unknown": unknown_count,
            "predicted_unknown_rate": _ratio(unknown_count, total),
            "reference_unknown": expected_unknown,
            "unknown_recall": per_language.get("und", {}).get("recall", 0.0),
        },
        "code_switch_detection": _code_switch_metrics(predictions),
        "confidence_calibration": _confidence_calibration(predictions),
        "confusion": {
            language: dict(sorted(row.items()))
            for language, row in sorted(confusion.items())
        },
        "predictions": predictions,
        "limitations": (
            "Lexical text-only evaluation, not an ASR/audio benchmark. Dataset metadata validation "
            "cannot prove consent, licensing, fluency, or that human review occurred. Synthetic "
            "smoke scores are regression plumbing only, never production-accuracy estimates. "
            "Reviewed datasets default to the held-out test split; do not tune on test results."
        ),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("tests/fixtures/multilingual_language_smoke_v1.json"),
    )
    parser.add_argument(
        "--split",
        choices=("all", "train", "validation", "development", "test", "smoke"),
        help="Split to evaluate; reviewed datasets default to test, smoke datasets to all",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    try:
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
        report = evaluate(corpus, split=args.split)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote language-ID report to {args.output}", file=sys.stderr)
        else:
            print(rendered, end="")
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"benchmark-language-id: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
