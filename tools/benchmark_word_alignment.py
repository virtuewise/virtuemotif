"""Evaluate word-level alignment against a rights-cleared reviewed reference corpus.

This evaluator does not transcribe or align audio. It compares supplied predictions
with independently annotated references and refuses smoke/unreviewed datasets.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

from tools.validate_language_dataset import REVIEWED_STATUS, validate_corpus


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(quantile * len(ordered)) - 1)
    return round(ordered[index], 4)


def _normalise_token(value: Any) -> str:
    return " ".join(str(value).casefold().replace("’", "'").split())


def evaluate_alignment(corpus: Any, predictions: Any, split: str = "test") -> dict[str, Any]:
    """Report token match and boundary error by language on a reviewed split."""
    errors = validate_corpus(corpus)
    if errors:
        raise ValueError("invalid reference corpus: " + "; ".join(errors))
    if corpus.get("status") != REVIEWED_STATUS:
        raise ValueError("word-alignment evaluation requires a reviewed rights-cleared corpus")
    if split not in {"test", "validation", "development", "all"}:
        raise ValueError("split must be test, validation, development, or all")
    if not isinstance(predictions, dict):
        raise ValueError("predictions must be an object keyed by example id")

    selected = [
        item for item in corpus["examples"]
        if split == "all" or item.get("split") == split
    ]
    if not selected:
        raise ValueError(f"requested split {split!r} has no examples")

    metrics: dict[str, dict[str, Any]] = {}
    overall: dict[str, Any] = {"examples": 0, "reference_words": 0, "predicted_words": 0,
                               "matched_words": 0, "start_errors": [], "end_errors": []}
    for example in selected:
        language = example["language"]
        reference = example.get("words")
        predicted = predictions.get(example["id"])
        if not isinstance(reference, list) or not reference:
            raise ValueError(f"example {example['id']!r} requires reference words")
        if not isinstance(predicted, list):
            raise ValueError(f"missing predicted word list for {example['id']!r}")

        bucket = metrics.setdefault(language, {
            "examples": 0, "reference_words": 0, "predicted_words": 0, "matched_words": 0,
            "start_errors": [], "end_errors": [],
        })
        bucket["examples"] += 1
        overall["examples"] += 1
        bucket["reference_words"] += len(reference)
        bucket["predicted_words"] += len(predicted)
        overall["reference_words"] += len(reference)
        overall["predicted_words"] += len(predicted)

        for index, (ref_word, pred_word) in enumerate(zip(reference, predicted)):
            if not isinstance(ref_word, dict) or not isinstance(pred_word, dict):
                raise ValueError(f"example {example['id']!r} word {index} must be an object")
            if _normalise_token(ref_word.get("text", "")) != _normalise_token(pred_word.get("text", "")):
                continue
            try:
                ref_start, ref_end = float(ref_word["start"]), float(ref_word["end"])
                pred_start, pred_end = float(pred_word["start"]), float(pred_word["end"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"example {example['id']!r} word {index} has invalid timestamps") from exc
            values = (ref_start, ref_end, pred_start, pred_end)
            if not all(math.isfinite(value) for value in values):
                raise ValueError(f"example {example['id']!r} word {index} has non-finite timestamps")
            if ref_start < 0 or ref_end <= ref_start or pred_start < 0 or pred_end <= pred_start:
                raise ValueError(f"example {example['id']!r} word {index} has invalid interval")
            start_error = abs(pred_start - ref_start)
            end_error = abs(pred_end - ref_end)
            bucket["start_errors"].append(start_error)
            bucket["end_errors"].append(end_error)
            bucket["matched_words"] += 1
            overall["start_errors"].append(start_error)
            overall["end_errors"].append(end_error)
            overall["matched_words"] += 1

    def finish(bucket: dict[str, Any]) -> dict[str, Any]:
        matched = bucket["matched_words"]
        ref_count = bucket["reference_words"]
        pred_count = bucket["predicted_words"]
        start_errors = bucket.pop("start_errors")
        end_errors = bucket.pop("end_errors")
        return {
            **bucket,
            "word_match_recall": round(matched / ref_count, 6) if ref_count else 0.0,
            "word_match_precision": round(matched / pred_count, 6) if pred_count else 0.0,
            "start_boundary_mae_seconds": round(statistics.mean(start_errors), 4) if start_errors else None,
            "start_boundary_median_absolute_error_seconds": _percentile(start_errors, 0.5) if start_errors else None,
            "start_boundary_p95_absolute_error_seconds": _percentile(start_errors, 0.95) if start_errors else None,
            "end_boundary_mae_seconds": round(statistics.mean(end_errors), 4) if end_errors else None,
            "end_boundary_median_absolute_error_seconds": _percentile(end_errors, 0.5) if end_errors else None,
            "end_boundary_p95_absolute_error_seconds": _percentile(end_errors, 0.95) if end_errors else None,
            "warning": "Word timing metrics only describe matched tokens; inspect unmatched tokens and audio manually.",
        }

    return {
        "schema_version": 1,
        "evidence_level": "human_reviewed_rights_cleared_reference_alignment",
        "dataset_id": corpus["dataset_id"],
        "evaluated_split": split,
        "per_language": {language: finish(bucket) for language, bucket in sorted(metrics.items())},
        "overall": finish(overall),
        "limitations": [
            "This evaluator compares supplied predictions; it does not run ASR or force alignment.",
            "Word position pairing is used; token insertions/deletions can shift later pairs and require manual inspection.",
            "Reference rights, consent, annotation quality, and native-speaker review must be independently verified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--split", default="test")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        corpus = json.loads(args.references.read_text(encoding="utf-8"))
        predictions = json.loads(args.predictions.read_text(encoding="utf-8"))
        report = evaluate_alignment(corpus, predictions, split=args.split)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"word-alignment-benchmark: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
