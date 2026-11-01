"""Repeatable lexical language-ID smoke benchmark (not an ASR/audio benchmark)."""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.lyrics_engine import detect_text_language


def evaluate(corpus: Any) -> dict[str, Any]:
    if not isinstance(corpus, dict) or corpus.get("schema_version") != 1:
        raise ValueError("corpus must be a schema_version 1 object")
    examples = corpus.get("examples")
    if not isinstance(examples, list) or not examples:
        raise ValueError("corpus must contain a non-empty examples array")
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    predictions = []
    for index, example in enumerate(examples):
        if not isinstance(example, dict) or not isinstance(example.get("text"), str):
            raise TypeError(f"example {index} must contain text as a string")
        expected = example.get("language")
        if not isinstance(expected, str) or not expected:
            raise ValueError(f"example {index} must contain a language label")
        predicted = detect_text_language(example["text"])
        actual = str(predicted["language"])
        counts[expected]["total"] += 1
        counts[expected]["correct"] += int(actual == expected)
        confusion[expected][actual] += 1
        predictions.append({
            "id": str(example.get("id", index)),
            "expected": expected,
            "predicted": actual,
            "correct": actual == expected,
            "confidence": predicted["confidence"],
            "method": predicted["method"],
        })
    total = len(predictions)
    correct = sum(item["correct"] for item in predictions)
    return {
        "schema_version": 1,
        "dataset_id": str(corpus.get("dataset_id", "unnamed")),
        "dataset_status": str(corpus.get("status", "unspecified")),
        "examples": total,
        "correct": correct,
        "accuracy": round(correct / total, 6),
        "per_language": {
            language: {
                "correct": values["correct"],
                "total": values["total"],
                "accuracy": round(values["correct"] / values["total"], 6),
            }
            for language, values in sorted(counts.items())
        },
        "confusion": {language: dict(sorted(row.items())) for language, row in sorted(confusion.items())},
        "predictions": predictions,
        "limitations": (
            "Lexical text-only smoke test. This synthetic corpus is not native-speaker reviewed, "
            "does not evaluate audio/ASR, and must not be used as a production-accuracy claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("tests/fixtures/multilingual_language_smoke_v1.json"))
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    try:
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
        report = evaluate(corpus)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote language-ID smoke report to {args.output}", file=sys.stderr)
        else:
            print(rendered, end="")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"benchmark-language-id: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
