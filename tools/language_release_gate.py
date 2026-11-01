"""Fail-closed structural gate for reviewed language evaluation releases.

This gate checks declared metadata and split integrity. It cannot independently
verify consent, licensing, annotator fluency, or whether review actually occurred.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.validate_language_dataset import REVIEWED_STATUS, validate_corpus


def release_errors(corpus: Any) -> list[str]:
    """Return release-blocking errors; never treat smoke fixtures as release data."""
    errors = validate_corpus(corpus)
    if not isinstance(corpus, dict):
        return errors
    if corpus.get("status") != REVIEWED_STATUS:
        errors.append(
            "release requires status "
            f"{REVIEWED_STATUS!r}; synthetic smoke datasets are not releasable"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "corpus",
        type=Path,
        help="Path to the candidate reviewed dataset JSON",
    )
    args = parser.parse_args()
    try:
        corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"language-release-gate: {exc}", file=sys.stderr)
        return 2

    errors = release_errors(corpus)
    if errors:
        for error in errors:
            print(f"BLOCKED: {error}", file=sys.stderr)
        print("Language evaluation release gate: BLOCKED", file=sys.stderr)
        return 1

    print(
        "Language evaluation release gate: STRUCTURALLY VALID "
        f"(dataset={corpus['dataset_id']}, examples={len(corpus['examples'])})"
    )
    print(
        "LIMITATION: metadata checks cannot prove rights, consent, reviewer "
        "qualifications, adjudication quality, or real-world representativeness."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
