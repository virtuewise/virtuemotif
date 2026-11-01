"""Validate and inspect VirtueMotif's reviewed free-dataset catalog.

This tool intentionally does not download or copy datasets. Source terms and
permissions must be checked before an operator obtains data. Common Voice
archives must not be re-hosted, and speaker identification is prohibited.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "data" / "dataset_catalog.json"
REQUIRED_FIELDS = {
    "id",
    "name",
    "languages",
    "license",
    "task",
    "media_type",
    "source_url",
    "source_record_type",
    "source_verified_date",
    "training_use",
    "redistribution",
    "restrictions",
    "limitations",
}
ALLOWED_LICENSES = {"CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"}


class CatalogError(ValueError):
    """Raised when the dataset catalog is incomplete or unsafe."""


def validate_catalog(payload: Any) -> list[str]:
    """Return validation errors; an empty list means the catalog is well-formed."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["catalog root must be a JSON object"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    policy = payload.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        for key in (
            "download_requires_explicit_operator_action",
            "never_commit_dataset_audio_or_raw_corpus_exports",
            "never_rehost_or_redistribute_common_voice_archives",
            "never_attempt_speaker_identification",
            "speech_data_is_not_a_singing_benchmark",
        ):
            if policy.get(key) is not True:
                errors.append(f"policy.{key} must be true")

    datasets = payload.get("datasets")
    if not isinstance(datasets, list) or not datasets:
        return errors + ["datasets must be a non-empty list"]

    seen_ids: set[str] = set()
    for index, dataset in enumerate(datasets):
        prefix = f"datasets[{index}]"
        if not isinstance(dataset, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED_FIELDS - dataset.keys()
        if missing:
            errors.append(f"{prefix} missing fields: {', '.join(sorted(missing))}")
            continue

        dataset_id = dataset.get("id")
        if not isinstance(dataset_id, str) or not dataset_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif dataset_id in seen_ids:
            errors.append(f"duplicate dataset id: {dataset_id}")
        else:
            seen_ids.add(dataset_id)

        languages = dataset.get("languages")
        if (
            not isinstance(languages, list)
            or not languages
            or any(not isinstance(code, str) or not code.strip() for code in languages)
        ):
            errors.append(f"{prefix}.languages must be a non-empty list of language codes")

        license_id = dataset.get("license")
        if license_id not in ALLOWED_LICENSES:
            errors.append(
                f"{prefix}.license is not allow-listed; verify the license before inclusion"
            )

        source_url = dataset.get("source_url")
        parsed_url = urlparse(source_url) if isinstance(source_url, str) else None
        if not parsed_url or parsed_url.scheme != "https" or not parsed_url.netloc:
            errors.append(f"{prefix}.source_url must be an absolute HTTPS URL")

        if dataset.get("source_record_type") not in {"dataset_record", "catalog_listing"}:
            errors.append(f"{prefix}.source_record_type must identify the kind of source URL")

        for field in ("training_use", "redistribution"):
            if not isinstance(dataset.get(field), str) or not dataset[field].strip():
                errors.append(f"{prefix}.{field} must explain applicable rights/limits")

        for field in ("restrictions", "limitations"):
            value = dataset.get(field)
            if not isinstance(value, list) or not value or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                errors.append(f"{prefix}.{field} must be a non-empty list of notes")

        if dataset.get("media_type") == "speech" and not any(
            "not singing" in note.lower() for note in dataset.get("limitations", [])
            if isinstance(note, str)
        ):
            errors.append(f"{prefix} speech data must explicitly state that it is not singing")

    return errors


def load_catalog(path: Path = DEFAULT_CATALOG) -> dict[str, Any]:
    """Load JSON and raise CatalogError for invalid JSON or catalog schema."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read catalog {path}: {exc}") from exc
    errors = validate_catalog(payload)
    if errors:
        raise CatalogError("\n".join(errors))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--language", help="Filter by ISO language code, e.g. sn, zu, xh, en")
    args = parser.parse_args()

    try:
        catalog = load_catalog(args.catalog)
    except CatalogError as exc:
        parser.error(str(exc))

    datasets = catalog["datasets"]
    if args.language:
        datasets = [
            dataset for dataset in datasets if args.language in dataset["languages"]
        ]
    if not datasets:
        print("No catalog entries matched.")
        return 1

    for dataset in datasets:
        print(
            f'{dataset["id"]}: {dataset["name"]} '
            f'[{", ".join(dataset["languages"])}; {dataset["license"]}; '
            f'{dataset["media_type"]}]\n'
            f'  Source: {dataset["source_url"]}\n'
            f'  Limitations: {" ".join(dataset["limitations"])}'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
