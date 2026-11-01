"""Validate multilingual language-ID dataset structure and governance metadata."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SMOKE_STATUS = "synthetic_smoke_only_requires_native_speaker_review"
REVIEWED_STATUS = "native_speaker_reviewed_rights_cleared"
ALLOWED_SPLITS = {"smoke", "train", "validation", "test", "development"}
REQUIRED_RELEASE_LANGUAGES = {"sn", "nd", "zu", "en", "mul"}


def validate_corpus(corpus: Any) -> list[str]:
    """Return deterministic validation errors; this cannot verify human claims are true."""
    errors: list[str] = []
    if not isinstance(corpus, dict):
        return ["corpus must be a JSON object"]
    if corpus.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    dataset_id = corpus.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        errors.append("dataset_id must be a non-empty string")
    status = corpus.get("status")
    valid_statuses = {SMOKE_STATUS, REVIEWED_STATUS}
    if not isinstance(status, str) or status not in valid_statuses:
        errors.append(f"status must be {SMOKE_STATUS!r} or {REVIEWED_STATUS!r}")

    labels = corpus.get("labels")
    if not isinstance(labels, list) or not labels or any(
        not isinstance(label, str) or not label.strip() for label in labels
    ):
        errors.append("labels must be a non-empty array of non-empty strings")
        labels_set: set[str] = set()
    else:
        labels_set = set(labels)
        if len(labels_set) != len(labels):
            errors.append("labels must not contain duplicates")

    examples = corpus.get("examples")
    if not isinstance(examples, list) or not examples:
        errors.append("examples must be a non-empty array")
        examples = []

    seen_ids: set[str] = set()
    source_splits: dict[str, set[str]] = {}
    speaker_splits: dict[str, set[str]] = {}
    for index, example in enumerate(examples):
        prefix = f"examples[{index}]"
        if not isinstance(example, dict):
            errors.append(f"{prefix} must be an object")
            continue
        example_id = example.get("id")
        if not isinstance(example_id, str) or not example_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif example_id in seen_ids:
            errors.append(f"{prefix}.id duplicates {example_id!r}")
        else:
            seen_ids.add(example_id)
        text = example.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{prefix}.text must be a non-empty string")
        language = example.get("language")
        if not isinstance(language, str) or not language.strip():
            errors.append(f"{prefix}.language must be a non-empty string")
        elif labels_set and language not in labels_set:
            errors.append(f"{prefix}.language {language!r} is absent from labels")
        split = example.get("split")
        if not isinstance(split, str) or split not in ALLOWED_SPLITS:
            errors.append(f"{prefix}.split must be one of {sorted(ALLOWED_SPLITS)}")
        if status == REVIEWED_STATUS:
            for field in ("source_id", "speaker_id", "review_status", "consent_ref"):
                value = example.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix}.{field} is required for reviewed datasets")
            source_id = example.get("source_id")
            if isinstance(source_id, str) and source_id.strip() and isinstance(split, str):
                source_splits.setdefault(source_id, set()).add(split)
            speaker_id = example.get("speaker_id")
            if isinstance(speaker_id, str) and speaker_id.strip() and isinstance(split, str):
                speaker_splits.setdefault(speaker_id, set()).add(split)
            if example.get("review_status") != "native_speaker_reviewed":
                errors.append(f"{prefix}.review_status must be 'native_speaker_reviewed'")
            reviewer_ids = example.get("reviewer_ids")
            if not isinstance(reviewer_ids, list) or not reviewer_ids or any(
                not isinstance(item, str) or not item.strip() for item in reviewer_ids
            ):
                errors.append(f"{prefix}.reviewer_ids must contain pseudonymous reviewer IDs")

    if status == REVIEWED_STATUS:
        governance = corpus.get("governance")
        if not isinstance(governance, dict):
            errors.append("governance object is required for reviewed datasets")
        else:
            required_values = {
                "rights_status": "rights_cleared",
                "consent_status": "documented",
                "review_status": "native_speaker_reviewed",
            }
            for field, expected in required_values.items():
                if governance.get(field) != expected:
                    errors.append(f"governance.{field} must be {expected!r}")
            policy = governance.get("adjudication_policy")
            if not isinstance(policy, str) or not policy.strip():
                errors.append("governance.adjudication_policy must be documented")
            split_policy = governance.get("split_policy")
            if not isinstance(split_policy, str) or not split_policy.strip():
                errors.append("governance.split_policy must document source/speaker separation")
        split_names = {
            example["split"]
            for example in examples
            if isinstance(example, dict) and isinstance(example.get("split"), str)
        }
        if not {"train", "test"} <= split_names:
            errors.append("reviewed datasets must contain separate train and test splits")
        release_profile = governance.get("release_profile") if isinstance(governance, dict) else None
        if release_profile == "multilingual_music_v1":
            test_languages = {
                example["language"]
                for example in examples
                if isinstance(example, dict)
                and example.get("split") == "test"
                and isinstance(example.get("language"), str)
            }
            missing_test_languages = REQUIRED_RELEASE_LANGUAGES - test_languages
            if missing_test_languages:
                errors.append(
                    "reviewed test split is missing required release cohorts: "
                    + ", ".join(sorted(missing_test_languages))
                )
        for source_id, splits in source_splits.items():
            if len(splits) > 1:
                errors.append(f"source_id {source_id!r} crosses dataset splits")
        for speaker_id, splits in speaker_splits.items():
            if len(splits) > 1:
                errors.append(f"speaker_id {speaker_id!r} crosses dataset splits")

    if status == SMOKE_STATUS:
        for index, example in enumerate(examples):
            if isinstance(example, dict) and example.get("split") != "smoke":
                errors.append(f"examples[{index}].split must be 'smoke' for synthetic smoke datasets")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "corpus",
        nargs="?",
        type=Path,
        default=Path("tests/fixtures/multilingual_language_smoke_v1.json"),
    )
    args = parser.parse_args()
    try:
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"validate-language-dataset: {exc}", file=sys.stderr)
        return 2
    errors = validate_corpus(corpus)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"Valid schema structure: dataset={corpus['dataset_id']} "
        f"status={corpus['status']} examples={len(corpus['examples'])}"
    )
    if corpus["status"] == SMOKE_STATUS:
        print(
            "WARNING: synthetic smoke data only; this validator does not verify "
            "speaker review, consent, licensing, or real-world accuracy.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
