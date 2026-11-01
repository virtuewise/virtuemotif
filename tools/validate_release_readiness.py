#!/usr/bin/env python3
"""Fail closed when repository release prerequisites are not evidenced."""
from __future__ import annotations

import csv
import re
import subprocess
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

    evidence_path = ROOT / "docs" / "release-evidence-record.md"
    if not evidence_path.is_file():
        failures.append("docs/release-evidence-record.md is missing")
    else:
        evidence = evidence_path.read_text(encoding="utf-8")
        decision_line = next(
            (line for line in evidence.splitlines() if line.strip().startswith("- Decision:")),
            "",
        )
        if decision_line.split("`")[-2:-1] != ["APPROVED"]:
            failures.append("release evidence decision must be explicitly APPROVED by the release owner")

        commit_match = re.search(
            r"^\s*-\s*Release commit SHA:\s*([0-9a-fA-F]{40})\s*$",
            evidence,
            re.MULTILINE,
        )
        if not commit_match:
            failures.append("release evidence must record the exact 40-character release commit SHA")
        else:
            try:
                current_commit = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
            except (OSError, subprocess.CalledProcessError) as exc:
                failures.append(f"cannot resolve checked-out release commit: {exc}")
            else:
                if commit_match.group(1).lower() != current_commit.lower():
                    failures.append(
                        "release evidence commit SHA does not match the checked-out release commit"
                    )

        required_signoffs = (
            "Required automated checks passed on the candidate commit.",
            "All distributed assets have verified permission and required attribution.",
            "Held-out multilingual results are based on genuinely reviewed, rights-cleared samples.",
            "Human visual/audio review is complete for supported output formats.",
            "Reproducibility and rollback have been demonstrated.",
            "Known limitations are documented and user-facing claims are accurate.",
            "Release owner approved this exact commit.",
        )
        for signoff in required_signoffs:
            pattern = r"^\s*-\s*\\[x\\]\s+" + re.escape(signoff) + r"\s*$"
            if not re.search(pattern, evidence, re.MULTILINE | re.IGNORECASE):
                failures.append(f"release evidence sign-off is incomplete: {signoff}")

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
