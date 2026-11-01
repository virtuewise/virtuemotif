"""Track language changes across timestamped lyric segments without hiding uncertainty."""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from typing import Any

DEFAULT_MIN_CONFIDENCE = 0.55


def _normalise_confidence(value: Any) -> float | None:
    try:
        confidence = float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
    if confidence is not None and (
        not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0
    ):
        return None
    return confidence


def _normalise_review_reasons(value: Any) -> list[str]:
    """Normalise caller-supplied review reasons without splitting strings into characters."""
    if value is None:
        return []
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, Iterable) or isinstance(values, Mapping):
        return ["invalid_review_reasons_metadata"]
    reasons: list[str] = []
    for item in values:
        if not isinstance(item, str):
            return ["invalid_review_reasons_metadata"]
        reason = item.strip()
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def segment_requires_review(
    segment: Mapping[str, Any], *, min_confidence: float = DEFAULT_MIN_CONFIDENCE
) -> bool:
    """Return whether one segment warrants review using timeline's shared policy."""
    if not math.isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be a finite number between 0 and 1")
    language = str(segment.get("language") or "und")
    confidence = _normalise_confidence(segment.get("language_confidence"))
    short = len(str(segment.get("text") or "").split()) <= 2
    reasons = _normalise_review_reasons(segment.get("review_reasons"))
    return bool(segment.get("review_required", False) or reasons) or (
        language in {"und", "mul"}
        or confidence is None
        or confidence < min_confidence
        or short
    )


def build_language_timeline(
    segments: Iterable[Mapping[str, Any]],
    *,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
) -> dict[str, Any]:
    """Summarize segment language transitions while preserving original segment evidence.

    Confidence is treated as a heuristic/model signal, not a calibrated probability.
    Short/low-confidence or unknown segments are marked for review, not smoothed away.
    """
    if not math.isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be a finite number between 0 and 1")

    rows: list[dict[str, Any]] = []
    previous_end = -1.0
    previous_language: str | None = None
    transitions: list[dict[str, Any]] = []

    for index, segment in enumerate(segments):
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"segment {index} must contain numeric start and end") from exc
        if not math.isfinite(start) or not math.isfinite(end):
            raise ValueError(f"segment {index} timestamps must be finite numbers")
        if start < 0 or end < start:
            raise ValueError(f"segment {index} has invalid timestamp interval")
        if start < previous_end:
            raise ValueError(f"segment {index} starts before the previous segment ends")

        language = str(segment.get("language") or "und")
        confidence = _normalise_confidence(segment.get("language_confidence"))
        text = str(segment.get("text") or "")
        is_short = len(text.split()) <= 2
        supplied_reasons = _normalise_review_reasons(segment.get("review_reasons"))
        generated_reasons = [
            reason
            for reason, condition in (
                ("unknown_or_mixed_language", language in {"und", "mul"}),
                ("confidence_missing", confidence is None),
                ("low_confidence", confidence is not None and confidence < min_confidence),
                ("short_segment", is_short),
            )
            if condition
        ]
        uncertainty_reasons = list(dict.fromkeys([*supplied_reasons, *generated_reasons]))
        if segment.get("review_required", False) and not uncertainty_reasons:
            uncertainty_reasons.append("upstream_review_required")
        if "invalid_review_reasons_metadata" in uncertainty_reasons:
            # Malformed upstream metadata must not silently erase a review signal.
            uncertainty_reasons = [
                *uncertainty_reasons,
                "upstream_review_metadata_invalid",
            ]
            uncertainty_reasons = list(dict.fromkeys(uncertainty_reasons))

        uncertain = bool(uncertainty_reasons)
        row = {
            "index": index,
            "start": round(start, 3),
            "end": round(end, 3),
            "language": language,
            "language_confidence": confidence,
            "language_method": segment.get("language_method", "unknown"),
            "text": text,
            "review_required": uncertain,
            "uncertainty_reasons": uncertainty_reasons,
        }
        rows.append(row)

        if previous_language is not None and language != previous_language:
            previous_segment_uncertain = rows[-2]["review_required"]
            transitions.append({
                "at": round(start, 3),
                "from": previous_language,
                "to": language,
                "candidate": True,
                "review_required": previous_segment_uncertain or row["review_required"],
            })
        previous_language = language
        previous_end = end

    counts: dict[str, int] = {}
    for row in rows:
        language = str(row["language"])
        counts[language] = counts.get(language, 0) + 1

    return {
        "schema_version": 1,
        "confidence_semantics": (
            "Model/heuristic signal; not a calibrated probability unless separately validated."
        ),
        "min_confidence": min_confidence,
        "segments": rows,
        "language_counts": dict(sorted(counts.items())),
        "transitions": transitions,
        "review_required": any(row["review_required"] for row in rows),
    }
