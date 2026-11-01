#!/usr/bin/env python3
"""Fail closed when repository release prerequisites are not evidenced."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    failures: list[str] = []
    license_file = ROOT / "LICENSE"
    if not license_file.is_file() or not license_file.read_text(encoding="utf-8").strip():
        failures.append("root LICENSE is missing or empty; owner must choose and document the project license")

    ledger = ROOT / "docs" / "asset-provenance-ledger.csv"
    if not ledger.is_file():
        failures.append("docs/asset-provenance-ledger.csv is missing")
    else:
        with ledger.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"path", "status"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                failures.append("asset provenance ledger must contain path and status columns")
            else:
                rows = list(reader)
                if not rows:
                    failures.append("asset provenance ledger is empty; release requires an explicit reviewed inventory")
                for row in rows:
                    path = (row.get("path") or "").strip()
                    status = (row.get("status") or "").strip().upper()
                    if not path:
                        failures.append("asset provenance ledger contains a row without a path")
                    if status not in {"VERIFIED", "CLEARED", "REMOVED"}:
                        failures.append(f"asset {path or '<unknown>'} has non-cleared status {status or '<empty>'}")
                    if status in {"VERIFIED", "CLEARED"}:
                        evidence_fields = ("creator_or_rights_holder", "source_url_or_record", "license_or_permission", "reviewer")
                        missing = [field for field in evidence_fields if not (row.get(field) or "").strip()]
                        if missing:
                            failures.append(f"asset {path} is marked {status} but lacks evidence fields: {', '.join(missing)}")
                    if status == "REMOVED" and path and (ROOT / path).exists():
                        failures.append(f"asset {path} is marked REMOVED but still exists in the repository")

    changelog = ROOT / "CHANGELOG.md"
    if not changelog.is_file() or "## [Unreleased]" not in changelog.read_text(encoding="utf-8"):
        failures.append("CHANGELOG.md must contain an Unreleased section")

    if failures:
        print("Release readiness BLOCKED:")
        for failure in failures:
            print(f"- {failure}")
        print("Resolve each item with owner-approved evidence; do not bypass this gate.")
        return 1

    print("Release readiness checks passed. This validates recorded evidence, not the truth of legal claims.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
