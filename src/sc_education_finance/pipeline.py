from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image

from .charts import render_all
from .config import load_config, resolve_path
from .download import fetch_sources, sha256
from .extract import extract_bea_rpp
from .metrics import competition_ranks
from .rights import assert_publication_allowed

OUTPUTS = [
    "data/curated/observations.csv",
    "data/curated/south-carolina-peer-comparison.csv",
    "data/curated/lineage.json",
    "docs/assets/figures/southeastern-rpp-trends.svg",
    "docs/assets/figures/southeastern-rpp-trends.png",
    "docs/assets/figures/south-carolina-peer-rpp.svg",
    "docs/assets/figures/south-carolina-peer-rpp.png",
]


def _validate_manifest(path: Path, snapshot: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError("The approved source manifest is missing. Run fetch first.")
    raw_manifest: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise ValueError("The approved source manifest is malformed.")
    manifest: dict[str, Any] = raw_manifest
    entries = manifest.get("sources", [])
    if not isinstance(entries, list) or len(entries) != 1 or not isinstance(entries[0], dict):
        raise ValueError("The public source manifest must contain one source record.")
    entry: dict[str, Any] = entries[0]
    if entry.get("source_id") != "bea":
        raise ValueError("The public source manifest must contain only the approved BEA source.")
    if entry.get("sha256") != sha256(snapshot):
        raise ValueError("The BEA source snapshot does not match its manifest hash.")
    return entry


def build(root: Path, destination: Path | None = None) -> list[Path]:
    """Validate rights, normalize BEA data, and render approved outputs."""
    config = load_config(root)
    source = assert_publication_allowed(config, "bea", derivative=True)
    source_dir = resolve_path(root, config["paths"]["source"])
    snapshot = source_dir / str(source["snapshot"])
    if not snapshot.exists():
        raise ValueError("The approved BEA snapshot is missing. Run fetch first.")
    manifest_entry = _validate_manifest(source_dir / "source-manifest.json", snapshot)

    first_year, last_year = (int(value) for value in config["analysis"]["years"])
    peers = set(config["analysis"]["peer_states"])
    records = extract_bea_rpp(
        snapshot,
        source_release=str(source["release"]),
        peers=peers,
        years=range(first_year, last_year + 1),
    )
    frame = pd.DataFrame([record.as_dict() for record in records]).sort_values(
        ["metric", "geography", "year"]
    )

    base = destination or root
    curated = base / str(config["paths"]["curated"])
    figures = base / str(config["paths"]["figures"])
    curated.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    frame.to_csv(
        curated / "observations.csv", index=False, lineterminator="\n", float_format="%.3f"
    )

    latest = frame[
        (frame["metric"] == "regional_price_parity_all_items")
        & (frame["year"] == last_year)
    ].sort_values("value", ascending=False).copy()
    latest["peer_rank"] = competition_ranks(latest["value"].tolist())
    sc_value = float(
        latest.loc[latest["geography"] == "South Carolina", "value"].iloc[0]
    )
    latest["difference_from_south_carolina"] = latest["value"] - sc_value
    latest.to_csv(
        curated / "south-carolina-peer-comparison.csv",
        index=False,
        lineterminator="\n",
        float_format="%.3f",
    )

    lineage = {
        "source_id": "bea",
        "source_release": str(source["release"]),
        "source_sha256": manifest_entry["sha256"],
        "rights_url": source["rights_url"],
        "approved_for_public_build": True,
    }
    with (curated / "lineage.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(lineage, indent=2) + "\n")
    render_all(
        frame,
        figures,
        start_year=int(config["analysis"]["trend_start_year"]),
        latest_year=last_year,
    )
    return [base / path for path in OUTPUTS]


def refresh(root: Path) -> list[Path]:
    fetch_sources(root, load_config(root))
    return build(root)


def check(root: Path) -> None:
    """Regenerate approved outputs offline and fail on drift."""
    with tempfile.TemporaryDirectory() as temporary:
        generated = build(root, Path(temporary))
        stale = []
        for path in generated:
            relative = path.relative_to(temporary)
            committed = root / relative
            if not committed.exists() or not _outputs_match(path, committed):
                stale.append(relative)
    if stale:
        names = ", ".join(str(path) for path in stale)
        raise RuntimeError(f"Generated outputs are stale: {names}")


def _outputs_match(generated: Path, committed: Path) -> bool:
    """Compare deterministic text bytes and decoded PNG pixels."""
    if generated.suffix.lower() != ".png":
        return generated.read_bytes() == committed.read_bytes()
    with Image.open(generated) as generated_image, Image.open(committed) as committed_image:
        return bool(
            generated_image.mode == committed_image.mode
            and generated_image.size == committed_image.size
            and generated_image.tobytes() == committed_image.tobytes()
        )
