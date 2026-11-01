"""Download an explicitly approved Mozilla Data Collective dataset."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.free_dataset_catalog import DEFAULT_CATALOG, CatalogError, load_catalog

DEFAULT_PROVENANCE_DIR = Path(".local-dataset-provenance")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inventory(path: Path) -> list[dict[str, Any]]:
    """Record file sizes and hashes without copying dataset contents."""
    files = (
        [path]
        if path.is_file()
        else sorted(item for item in path.rglob("*") if item.is_file())
    )
    return [
        {
            "relative_path": (
                item.name if path.is_file() else item.relative_to(path).as_posix()
            ),
            "size_bytes": item.stat().st_size,
            "sha256": _sha256(item),
        }
        for item in files
    ]


def acquire_dataset(
    catalog_id: str,
    *,
    confirm_terms_accepted: bool,
    catalog_path: Path = DEFAULT_CATALOG,
    provenance_dir: Path = DEFAULT_PROVENANCE_DIR,
) -> Path:
    """Download one approved catalog entry and write a local provenance record."""
    if not confirm_terms_accepted:
        raise ValueError(
            "refusing download: review and accept the current provider terms first, "
            "then pass --confirm-terms-accepted"
        )
    if not os.environ.get("MDC_API_KEY"):
        raise ValueError("MDC_API_KEY is required; create a credential in your MDC account")

    catalog = load_catalog(catalog_path)
    dataset = next((item for item in catalog["datasets"] if item["id"] == catalog_id), None)
    if dataset is None:
        raise ValueError(f"unknown catalog id: {catalog_id}")
    if dataset.get("license") != "CC0-1.0":
        raise ValueError("automatic acquisition is restricted to catalog entries marked CC0-1.0")
    provider_id = dataset.get("provider_dataset_id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("no verified provider dataset ID; resolve the source record first")

    try:
        from datacollective import download_dataset
    except ImportError as exc:
        raise RuntimeError(
            "install the official MDC SDK with python -m pip install datacollective"
        ) from exc

    result = download_dataset(provider_id)
    if result is None:
        raise RuntimeError("MDC SDK did not return a local dataset path")
    dataset_path = Path(result).expanduser().resolve()
    if not dataset_path.exists():
        raise RuntimeError(f"MDC SDK returned a path that does not exist: {dataset_path}")

    record = {
        "schema_version": 1,
        "catalog_id": catalog_id,
        "provider_dataset_id": provider_id,
        "name": dataset["name"],
        "license": dataset["license"],
        "source_url": dataset["source_url"],
        "source_verified_date": dataset["source_verified_date"],
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "local_path": str(dataset_path),
        "files": _inventory(dataset_path),
        "restrictions": dataset["restrictions"],
        "limitations": dataset["limitations"],
        "notice": "Local provenance only; never commit or re-host data files.",
    }
    provenance_dir.mkdir(parents=True, exist_ok=True)
    manifest = provenance_dir / f"{catalog_id}.json"
    manifest.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Dataset acquired to: {dataset_path}")
    print(f"Local provenance written to: {manifest}")
    return dataset_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--dataset", required=True, help="Catalog ID from dataset_catalog.json")
    parser.add_argument(
        "--confirm-terms-accepted",
        action="store_true",
        help="confirm that you reviewed and accepted the current provider terms",
    )
    parser.add_argument("--provenance-dir", type=Path, default=DEFAULT_PROVENANCE_DIR)
    args = parser.parse_args()
    try:
        acquire_dataset(
            args.dataset,
            confirm_terms_accepted=args.confirm_terms_accepted,
            catalog_path=args.catalog,
            provenance_dir=args.provenance_dir,
        )
    except (CatalogError, OSError, ValueError, RuntimeError) as exc:
        print(f"dataset-acquisition: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
