"""Download official public NHS benchmark sources with provenance receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources") if isinstance(payload, dict) else None
    if not isinstance(sources, list) or not sources:
        raise ValueError("Manifest must contain a non-empty 'sources' list")
    required = {"id", "name", "release", "url", "filename", "archive"}
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not required.issubset(source):
            raise ValueError(f"Each source must contain: {sorted(required)}")
        source_id = str(source["id"])
        if source_id in seen:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
        if urlparse(str(source["url"])).scheme != "https":
            raise ValueError(f"Source must use HTTPS: {source_id}")
        if source["archive"] not in (None, "zip"):
            raise ValueError(f"Unsupported archive type for {source_id}")
    return sources


def safe_extract_zip(archive: Path, destination: Path) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    extracted: list[str] = []
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        bundle.extractall(destination)
        extracted = [member.filename for member in bundle.infolist() if not member.is_dir()]
    return sorted(extracted)


def download_source(
    source: dict[str, Any],
    output_dir: Path,
    *,
    overwrite: bool = False,
    extract: bool = True,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / str(source["filename"])
    if overwrite or not target.is_file():
        temporary = target.with_suffix(target.suffix + ".part")
        temporary.unlink(missing_ok=True)
        with urllib.request.urlopen(str(source["url"]), timeout=120) as response:
            with temporary.open("wb") as stream:
                shutil.copyfileobj(response, stream)
        temporary.replace(target)
    extracted: list[str] = []
    if source["archive"] == "zip" and extract:
        extracted = safe_extract_zip(target, output_dir / str(source["id"]))
    return {
        "id": source["id"],
        "name": source["name"],
        "release": source["release"],
        "url": source["url"],
        "path": str(target.resolve()),
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "extracted_files": extracted,
    }


def fetch(
    manifest: Path,
    output_dir: Path,
    selected: set[str] | None = None,
    *,
    overwrite: bool = False,
    extract: bool = True,
) -> Path:
    sources = load_manifest(manifest)
    known = {str(source["id"]) for source in sources}
    if selected:
        unknown = selected.difference(known)
        if unknown:
            raise ValueError(f"Unknown source ids: {sorted(unknown)}")
        sources = [source for source in sources if str(source["id"]) in selected]
    receipts = [
        download_source(source, output_dir, overwrite=overwrite, extract=extract)
        for source in sources
    ]
    receipt_path = output_dir / "download_receipt.json"
    receipt_path.write_text(json.dumps({"sources": receipts}, indent=2), encoding="utf-8")
    return receipt_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download official public NHS benchmark sources")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("config/nhs_public_sources.json"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/nhs_public"))
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args()
    receipt = fetch(
        args.manifest,
        args.output_dir,
        set(args.sources) if args.sources else None,
        overwrite=args.overwrite,
        extract=not args.no_extract,
    )
    print(f"Saved provenance receipt to {receipt}")


if __name__ == "__main__":
    main()
