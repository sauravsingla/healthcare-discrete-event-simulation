from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "fetch_nhs_public_sources.py"
SPEC = importlib.util.spec_from_file_location("fetch_nhs_public_sources", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_manifest(path: Path, url: str, *, archive: str | None = None) -> None:
    path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "id": "sample",
                        "name": "Sample",
                        "release": "test",
                        "url": url,
                        "filename": "sample.zip" if archive else "sample.csv",
                        "archive": archive,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def test_manifest_requires_https(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, "http://example.test/sample.csv")
    with pytest.raises(ValueError, match="HTTPS"):
        MODULE.load_manifest(manifest)


def test_safe_extract_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.txt", "unsafe")
    with pytest.raises(ValueError, match="Unsafe ZIP member"):
        MODULE.safe_extract_zip(archive, tmp_path / "out")


def test_download_and_receipt_from_local_https_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_file = tmp_path / "source.csv"
    source_file.write_text("provider_code,value\nAAA,1\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, "https://example.test/sample.csv")

    class Response:
        def __enter__(self):
            return source_file.open("rb")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(MODULE.urllib.request, "urlopen", lambda *args, **kwargs: Response())
    receipt = MODULE.fetch(manifest, tmp_path / "downloads")
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    item = payload["sources"][0]
    assert item["id"] == "sample"
    assert item["bytes"] == source_file.stat().st_size
    assert len(item["sha256"]) == 64
    assert Path(item["path"]).is_file()


def test_selected_source_must_exist(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    write_manifest(manifest, "https://example.test/sample.csv")
    with pytest.raises(ValueError, match="Unknown source ids"):
        MODULE.fetch(manifest, tmp_path / "downloads", {"missing"})
