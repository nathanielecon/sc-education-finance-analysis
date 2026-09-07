from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from .config import resolve_path
from .extract import extract_rfa_salary_pdf
from .rights import approved_source_ids, assert_source_use_allowed


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_sources(root: Path, config: dict[str, Any]) -> Path:
    """Fetch sources approved for download and publish only approved snapshots."""
    raw_dir = resolve_path(root, config["paths"]["raw"])
    source_dir = resolve_path(root, config["paths"]["source"])
    raw_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, str]] = []

    for source_id in approved_source_ids(config, use="download"):
        source = assert_source_use_allowed(config, source_id, use="download")
        for required in ("data_url", "filename", "snapshot", "release"):
            if required not in source:
                raise ValueError(f"Approved source {source_id!r} lacks {required!r}.")
        response = requests.get(str(source["data_url"]), timeout=120)
        response.raise_for_status()
        archive_path = raw_dir / str(source["filename"])
        archive_path.write_bytes(response.content)
        snapshot_path = source_dir / str(source["snapshot"])
        if source_id == "bea":
            assert_source_use_allowed(config, source_id, use="raw_redistribution")
            with zipfile.ZipFile(archive_path) as archive:
                member = str(source.get("archive_member", ""))
                if member not in archive.namelist():
                    raise ValueError(f"Approved archive layout changed; missing {member!r}.")
                with archive.open(member) as source_handle:
                    source_text = source_handle.read().decode("utf-8-sig")
                normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
                with snapshot_path.open("w", encoding="utf-8", newline="\n") as target:
                    target.write(normalized)
        elif source_id == "rfa":
            assert_source_use_allowed(config, source_id, use="factual_extraction")
            records = extract_rfa_salary_pdf(
                archive_path,
                source_release=str(source["release"]),
                peer_states=set(config["analysis"]["salary_peer_states"]),
            )
            with snapshot_path.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(
                    target,
                    fieldnames=list(records[0].as_dict()),
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerows(record.as_dict() for record in records)
        else:
            raise ValueError(f"No fetch adapter is configured for {source_id!r}.")
        entries.append(
            {
                "source_id": source_id,
                "publisher": str(source["publisher"]),
                "data_url": str(source["data_url"]),
                "rights_url": str(source["rights_url"]),
                "retrieved_at": datetime.now(UTC).isoformat(),
                "release": str(source["release"]),
                "source_sha256": sha256(archive_path),
                "snapshot_sha256": sha256(snapshot_path),
                "content_type": response.headers.get(
                    "content-type", "application/octet-stream"
                ).split(";", 1)[0],
            }
        )

    manifest = source_dir / "source-manifest.json"
    with manifest.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"sources": entries}, indent=2) + "\n")
    return manifest
