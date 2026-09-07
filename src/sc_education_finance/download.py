from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from .config import resolve_path
from .rights import approved_source_ids, assert_publication_allowed


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_sources(root: Path, config: dict[str, Any]) -> Path:
    """Fetch only sources that pass the public-build rights gate."""
    raw_dir = resolve_path(root, config["paths"]["raw"])
    source_dir = resolve_path(root, config["paths"]["source"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, str]] = []

    for source_id in approved_source_ids(config):
        source = assert_publication_allowed(config, source_id, derivative=True)
        for required in ("data_url", "filename", "snapshot", "release"):
            if required not in source:
                raise ValueError(f"Approved source {source_id!r} lacks {required!r}.")
        response = requests.get(str(source["data_url"]), timeout=120)
        response.raise_for_status()
        archive_path = raw_dir / str(source["filename"])
        archive_path.write_bytes(response.content)
        snapshot_path = source_dir / str(source["snapshot"])
        with zipfile.ZipFile(archive_path) as archive:
            member = str(source.get("archive_member", ""))
            if member not in archive.namelist():
                raise ValueError(f"Approved archive layout changed; missing {member!r}.")
            with archive.open(member) as source_handle:
                source_text = source_handle.read().decode("utf-8-sig")
            normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
            with snapshot_path.open("w", encoding="utf-8", newline="\n") as target:
                target.write(normalized)
        entries.append(
            {
                "source_id": source_id,
                "publisher": str(source["publisher"]),
                "data_url": str(source["data_url"]),
                "rights_url": str(source["rights_url"]),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "release": str(source["release"]),
                "sha256": sha256(snapshot_path),
                "content_type": response.headers.get(
                    "content-type", "application/octet-stream"
                ).split(";", 1)[0],
            }
        )

    manifest = source_dir / "source-manifest.json"
    with manifest.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"sources": entries}, indent=2) + "\n")
    return manifest
