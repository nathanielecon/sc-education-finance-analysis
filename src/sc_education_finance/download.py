from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

from .config import resolve_path
from .extract import (
    BLS_SERIES,
    extract_bls_oews_response,
    extract_naep_responses,
    extract_rfa_salary_pdf,
)
from .rights import approved_source_ids, assert_source_use_allowed


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_records(path: Path, records: list[Any]) -> None:
    if not records:
        raise ValueError("A selected-fact snapshot cannot be empty.")
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=list(records[0].as_dict()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(record.as_dict() for record in records)


def _fetch_naep(
    source: Any, *, peers: set[str]
) -> tuple[bytes, list[Any], str]:
    state_codes = {
        "Alabama": "AL",
        "Arkansas": "AR",
        "Florida": "FL",
        "Georgia": "GA",
        "Kentucky": "KY",
        "Louisiana": "LA",
        "Mississippi": "MS",
        "North Carolina": "NC",
        "South Carolina": "SC",
        "Tennessee": "TN",
        "Virginia": "VA",
        "West Virginia": "WV",
    }
    if peers - set(state_codes):
        raise ValueError(f"NAEP jurisdiction codes are missing: {sorted(peers - set(state_codes))}")
    jurisdictions = ",".join(state_codes[state] for state in sorted(peers))
    queries = (
        ("mathematics", 4, "MRPCM"),
        ("reading", 4, "RRPCM"),
        ("mathematics", 8, "MRPCM"),
        ("reading", 8, "RRPCM"),
    )
    payloads: list[Mapping[str, Any]] = []
    for subject, grade, subscale in queries:
        params: dict[str, str | int] = {
            "type": "data",
            "subject": subject,
            "grade": grade,
            "subscale": subscale,
            "variable": "TOTAL",
            "jurisdiction": jurisdictions,
            "stattype": "ALC:AP",
            "Year": 2024,
        }
        response = requests.get(
            str(source["data_url"]),
            params=params,
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("The NAEP API returned a malformed response.")
        payloads.append(payload)
    raw = json.dumps({"responses": payloads}, indent=2, sort_keys=True).encode() + b"\n"
    records = extract_naep_responses(
        payloads,
        source_release=str(source["release"]),
        peers=peers,
    )
    return raw, records, "application/json"


def _fetch_bls(source: Any) -> tuple[bytes, list[Any], str]:
    response = requests.post(
        str(source["data_url"]),
        json={"seriesid": sorted(BLS_SERIES), "startyear": "2025", "endyear": "2025"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("The BLS API returned a malformed response.")
    raw = json.dumps(payload, indent=2, sort_keys=True).encode() + b"\n"
    records = extract_bls_oews_response(payload, source_release=str(source["release"]))
    return raw, records, "application/json"


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
        archive_path = raw_dir / str(source["filename"])
        snapshot_path = source_dir / str(source["snapshot"])
        download_content_type = "application/octet-stream"
        if source_id == "bea":
            response = requests.get(str(source["data_url"]), timeout=120)
            response.raise_for_status()
            download_content_type = response.headers.get(
                "content-type", "application/octet-stream"
            ).split(";", 1)[0]
            archive_path.write_bytes(response.content)
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
            response = requests.get(str(source["data_url"]), timeout=120)
            response.raise_for_status()
            download_content_type = response.headers.get(
                "content-type", "application/octet-stream"
            ).split(";", 1)[0]
            archive_path.write_bytes(response.content)
            assert_source_use_allowed(config, source_id, use="factual_extraction")
            records = extract_rfa_salary_pdf(
                archive_path,
                source_release=str(source["release"]),
                peer_states=set(config["analysis"]["salary_peer_states"]),
            )
            _write_records(snapshot_path, records)
        elif source_id == "bls":
            raw, records, content_type = _fetch_bls(source)
            download_content_type = content_type
            archive_path.write_bytes(raw)
            _write_records(snapshot_path, records)
        elif source_id == "naep":
            raw, records, content_type = _fetch_naep(
                source,
                peers=set(config["analysis"]["peer_states"]),
            )
            download_content_type = content_type
            archive_path.write_bytes(raw)
            _write_records(snapshot_path, records)
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
                "content_type": download_content_type,
                "acquisition": "download",
            }
        )

    for source_id, source in config["sources"].items():
        if not source.get("manual_snapshot"):
            continue
        assert_source_use_allowed(config, source_id, use="factual_extraction")
        snapshot_path = source_dir / str(source["snapshot"])
        if not snapshot_path.exists():
            raise ValueError(f"Manual selected-fact snapshot is missing for {source_id!r}.")
        entries.append(
            {
                "source_id": source_id,
                "publisher": str(source["publisher"]),
                "data_url": str(source["data_url"]),
                "rights_url": str(source["rights_url"]),
                "retrieved_at": str(source["reviewed_on"]),
                "release": str(source["release"]),
                "source_sha256": "not-downloaded",
                "snapshot_sha256": sha256(snapshot_path),
                "content_type": "text/csv",
                "acquisition": "manual_fact_verification",
                "verification_reference": str(source["verification_reference"]),
            }
        )

    manifest = source_dir / "source-manifest.json"
    with manifest.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"sources": entries}, indent=2) + "\n")
    return manifest
