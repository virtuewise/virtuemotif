"""Evaluate ASR text and language detection against a reviewed schema-v1 reference."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[\w’']+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return [token.casefold().replace("’", "'") for token in _TOKEN_RE.findall(text)]


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    """Return Levenshtein distance using O(len(hypothesis)) memory."""
    previous = list(range(len(hypothesis) + 1))
    for ref_index, ref_word in enumerate(reference, start=1):
        current = [ref_index]
        for hyp_index, hyp_word in enumerate(hypothesis, start=1):
            current.append(min(
                current[-1] + 1,
                previous[hyp_index] + 1,
                previous[hyp_index - 1] + (ref_word != hyp_word),
            ))
        previous = current
    return previous[-1]


def word_error_rate(reference_text: str, hypothesis_text: str) -> float | None:
    """Compute standard word error rate; return None when the reference has no words."""
    reference = _tokens(reference_text)
    hypothesis = _tokens(hypothesis_text)
    if not reference:
        return None
    return round(_edit_distance(reference, hypothesis) / len(reference), 6)


def _validated_segments(document: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError(f"{label} must be a schema_version 1 object")
    segments = document.get("segments")
    if not isinstance(segments, list):
        raise ValueError(f"{label} must contain a segments array")
    result = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"{label} segment {index} must be an object")
        text = segment.get("text")
        start, end = segment.get("start"), segment.get("end")
        if not isinstance(text, str):
            raise ValueError(f"{label} segment {index} text must be a string")
        if (
            isinstance(start, bool) or not isinstance(start, (int, float))
            or not math.isfinite(start)
            or isinstance(end, bool) or not isinstance(end, (int, float))
            or not math.isfinite(end) or start < 0 or end <= start
        ):
            raise ValueError(f"{label} segment {index} must have finite timing with 0 <= start < end")
        language = segment.get("language", segment.get("asr_language", "und"))
        if not isinstance(language, str) or not language.strip():
            language = "und"
        result.append({
            "text": text,
            "start": float(start),
            "end": float(end),
            "language": language.strip().casefold(),
        })
    return sorted(result, key=lambda item: (item["start"], item["end"]))


def evaluate_documents(reference_document: Any, hypothesis_document: Any) -> dict[str, Any]:
    """Compare normalized transcript text and overlap-aligned segment language labels."""
    reference = _validated_segments(reference_document, "reference")
    hypothesis = _validated_segments(hypothesis_document, "hypothesis")
    reference_text = " ".join(segment["text"] for segment in reference)
    hypothesis_text = " ".join(segment["text"] for segment in hypothesis)
    reference_words = _tokens(reference_text)
    hypothesis_words = _tokens(hypothesis_text)

    per_language: dict[str, dict[str, int]] = {}
    matched = correct = 0
    ignored_unknown = 0
    for predicted in hypothesis:
        best_reference = None
        best_overlap = 0.0
        for expected in reference:
            overlap = min(predicted["end"], expected["end"]) - max(
                predicted["start"], expected["start"]
            )
            if overlap > best_overlap:
                best_reference, best_overlap = expected, overlap
        if best_reference is None:
            continue
        expected_language = best_reference["language"]
        if expected_language in {"", "und", "unknown"}:
            ignored_unknown += 1
            continue
        actual_language = predicted["language"]
        bucket = per_language.setdefault(expected_language, {"correct": 0, "total": 0})
        bucket["total"] += 1
        matched += 1
        if actual_language == expected_language:
            bucket["correct"] += 1
            correct += 1

    return {
        "schema_version": 1,
        "reference_segments": len(reference),
        "hypothesis_segments": len(hypothesis),
        "reference_words": len(reference_words),
        "hypothesis_words": len(hypothesis_words),
        "word_error_rate": (
            round(_edit_distance(reference_words, hypothesis_words) / len(reference_words), 6)
            if reference_words else None
        ),
        "language_segments_scored": matched,
        "language_segments_correct": correct,
        "language_accuracy": round(correct / matched, 6) if matched else None,
        "unknown_reference_segments_ignored": ignored_unknown,
        "per_language": {
            language: {
                **counts,
                "accuracy": round(counts["correct"] / counts["total"], 6)
                if counts["total"] else None,
            }
            for language, counts in sorted(per_language.items())
        },
        "notes": (
            "Language labels are scored by maximum timestamp overlap. WER is calculated over "
            "the concatenated transcript; review reference quality and timing alignment before "
            "interpreting scores. No benchmark audio or language-accuracy claim is bundled."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare a reviewed lyric reference with a generated ASR JSON document."
    )
    parser.add_argument("reference", type=Path, help="Reviewed schema-v1 lyric JSON")
    parser.add_argument("hypothesis", type=Path, help="ASR JSON produced by tools.lyrics_engine")
    parser.add_argument("--output", type=Path, help="Optional path for the evaluation report JSON")
    args = parser.parse_args()
    try:
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
        hypothesis = json.loads(args.hypothesis.read_text(encoding="utf-8"))
        report = evaluate_documents(reference, hypothesis)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output is None:
            print(rendered, end="")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Wrote evaluation report to {args.output}", file=sys.stderr)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"evaluate-lyrics: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
