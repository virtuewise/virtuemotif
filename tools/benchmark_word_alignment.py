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


def _validated_words(words: Any, example_id: str, label: str) -> list[dict[str, Any]]:
    if not isinstance(words, list):
        raise TypeError(f"{label} words for {example_id!r} must be an array")
    result: list[dict[str, Any]] = []
    previous_start = -1.0
    for index, word in enumerate(words):
        if not isinstance(word, dict):
            raise TypeError(f"{label} word {index} for {example_id!r} must be an object")
        token = word.get("text")
        if not isinstance(token, str) or not _normalise_token(token):
            raise ValueError(f"{label} word {index} for {example_id!r} requires non-empty text")
        try:
            start, end = float(word["start"]), float(word["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{label} word {index} for {example_id!r} has invalid timestamps") from exc
        if (
            not math.isfinite(start) or not math.isfinite(end)
            or start < 0 or end <= start
        ):
            raise ValueError(f"{label} word {index} for {example_id!r} has invalid interval")
        if start < previous_start:
            raise ValueError(f"{label} words for {example_id!r} are out of order")
        previous_start = start
        result.append({"text": token, "normalised": _normalise_token(token), "start": start, "end": end})
    return result


def _match_word_sequences(
    reference: list[dict[str, Any]], predicted: list[dict[str, Any]]
) -> list[tuple[int, int]]:
    """Return maximum-cardinality ordered token matches (LCS), not positional zip pairs."""
    rows, columns = len(reference), len(predicted)
    lengths = [[0] * (columns + 1) for _ in range(rows + 1)]
    for i in range(rows - 1, -1, -1):
        for j in range(columns - 1, -1, -1):
            if reference[i]["normalised"] == predicted[j]["normalised"]:
                lengths[i][j] = 1 + lengths[i + 1][j + 1]
            else:
                lengths[i][j] = max(lengths[i + 1][j], lengths[i][j + 1])
    matches: list[tuple[int, int]] = []
    i = j = 0
    while i < rows and j < columns:
        if reference[i]["normalised"] == predicted[j]["normalised"]:
            matches.append((i, j))
            i += 1
            j += 1
        elif lengths[i + 1][j] >= lengths[i][j + 1]:
            i += 1
        else:
            j += 1
    return matches


def evaluate_alignment(corpus: Any, predictions: Any, split: str = "test") -> dict[str, Any]:
    """Report ordered token matches and boundary errors by language on a reviewed split."""
    errors = validate_corpus(corpus)
    if errors:
        raise ValueError("invalid reference corpus: " + "; ".join(errors))
    if corpus.get("status") != REVIEWED_STATUS:
        raise ValueError("word-alignment evaluation requires a reviewed rights-cleared corpus")
    if split not in {"test", "validation", "development", "all"}:
        raise ValueError("split must be test, validation, development, or all")
    if not isinstance(predictions, dict):
        raise TypeError("predictions must be an object keyed by example id")

    selected = [item for item in corpus["examples"] if split == "all" or item.get("split") == split]
    if not selected:
        raise ValueError(f"requested split {split!r} has no examples")

    metrics: dict[str, dict[str, Any]] = {}
    overall: dict[str, Any] = {
        "examples": 0, "reference_words": 0, "predicted_words": 0, "matched_words": 0,
        "start_errors": [], "end_errors": [],
    }
    for example in selected:
        language = example["language"]
        example_id = example["id"]
        reference = example.get("words")
        if not isinstance(reference, list) or not reference:
            raise ValueError(f"example {example_id!r} requires reference words")
        reference_words = _validated_words(reference, example_id, "reference")
        if example_id not in predictions:
            raise ValueError(f"missing predictions for {example_id!r}")
        predicted_words = _validated_words(predictions[example_id], example_id, "predicted")
        matches = _match_word_sequences(reference_words, predicted_words)

        bucket = metrics.setdefault(language, {
            "examples": 0, "reference_words": 0, "predicted_words": 0, "matched_words": 0,
            "insertions": 0, "deletions": 0, "start_errors": [], "end_errors": [],
        })
        for target in (bucket, overall):
            target["examples"] += 1
            target["reference_words"] += len(reference_words)
            target["predicted_words"] += len(predicted_words)
            target["matched_words"] += len(matches)
        bucket["insertions"] += len(predicted_words) - len(matches)
        bucket["deletions"] += len(reference_words) - len(matches)

        for ref_index, pred_index in matches:
            ref_word, pred_word = reference_words[ref_index], predicted_words[pred_index]
            start_error = abs(pred_word["start"] - ref_word["start"])
            end_error = abs(pred_word["end"] - ref_word["end"])
            bucket["start_errors"].append(start_error)
            bucket["end_errors"].append(end_error)
            overall["start_errors"].append(start_error)
            overall["end_errors"].append(end_error)

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
            "warning": "Boundary metrics cover ordered token matches only; inspect insertions, deletions, and audio manually.",
        }

    return {
        "schema_version": 1,
        "evidence_level": "human_reviewed_rights_cleared_reference_alignment",
        "dataset_id": corpus["dataset_id"],
        "evaluated_split": split,
        "matching_method": "longest_common_subsequence_normalized_tokens",
        "per_language": {language: finish(bucket) for language, bucket in sorted(metrics.items())},
        "overall": finish(overall),
        "limitations": [
            "This evaluator compares supplied predictions; it does not run ASR or force alignment.",
            "Ordered token matching avoids positional-shift timing errors but does not establish semantic equivalence.",
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
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
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
