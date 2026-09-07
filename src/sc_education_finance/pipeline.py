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
from .extract import RFA_METRIC, extract_bea_rpp, load_rfa_salary_snapshot
from .metrics import competition_ranks, purchasing_power
from .rights import assert_source_use_allowed

OUTPUTS = [
    "data/curated/observations.csv",
    "data/curated/south-carolina-peer-comparison.csv",
    "data/curated/teacher-salary-peer-comparison.csv",
    "data/curated/lineage.json",
    "docs/assets/figures/southeastern-rpp-trends.svg",
    "docs/assets/figures/southeastern-rpp-trends.png",
    "docs/assets/figures/south-carolina-peer-rpp.svg",
    "docs/assets/figures/south-carolina-peer-rpp.png",
    "docs/assets/figures/salary-trends.svg",
    "docs/assets/figures/salary-trends.png",
    "docs/assets/figures/peer-salary-estimates.svg",
    "docs/assets/figures/peer-salary-estimates.png",
    "docs/assets/figures/adjusted-salary-comparison.svg",
    "docs/assets/figures/adjusted-salary-comparison.png",
]


def _validate_manifest(path: Path, snapshots: dict[str, Path]) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise ValueError("The approved source manifest is missing. Run fetch first.")
    raw_manifest: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_manifest, dict):
        raise ValueError("The approved source manifest is malformed.")
    manifest: dict[str, Any] = raw_manifest
    entries = manifest.get("sources", [])
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("The public source manifest must contain source records.")
    indexed = {str(entry.get("source_id")): entry for entry in entries}
    if set(indexed) != set(snapshots):
        raise ValueError("The public source manifest does not match the approved snapshots.")
    for source_id, snapshot in snapshots.items():
        if indexed[source_id].get("snapshot_sha256") != sha256(snapshot):
            raise ValueError(f"The {source_id} snapshot does not match its manifest hash.")
        source_hash = str(indexed[source_id].get("source_sha256", ""))
        if len(source_hash) != 64:
            raise ValueError(f"The {source_id} source hash is missing or malformed.")
    return indexed


def build(root: Path, destination: Path | None = None) -> list[Path]:
    """Validate sources, normalize data, and render the committed outputs."""
    config = load_config(root)
    bea_source = assert_source_use_allowed(config, "bea", use="factual_extraction")
    assert_source_use_allowed(config, "bea", use="derivative_visualization")
    rfa_source = assert_source_use_allowed(config, "rfa", use="factual_extraction")
    assert_source_use_allowed(config, "rfa", use="derivative_visualization")
    source_dir = resolve_path(root, config["paths"]["source"])
    snapshots = {
        "bea": source_dir / str(bea_source["snapshot"]),
        "rfa": source_dir / str(rfa_source["snapshot"]),
    }
    missing = [source_id for source_id, path in snapshots.items() if not path.exists()]
    if missing:
        raise ValueError(f"Approved source snapshots are missing: {missing}. Run fetch first.")
    manifest_entries = _validate_manifest(source_dir / "source-manifest.json", snapshots)

    first_year, last_year = (int(value) for value in config["analysis"]["years"])
    peers = set(config["analysis"]["peer_states"])
    bea_records = extract_bea_rpp(
        snapshots["bea"],
        source_release=str(bea_source["release"]),
        peers=peers,
        years=range(first_year, last_year + 1),
    )
    salary_peers = set(config["analysis"]["salary_peer_states"])
    rfa_records = load_rfa_salary_snapshot(
        snapshots["rfa"],
        source_release=str(rfa_source["release"]),
        peer_states=salary_peers,
    )
    frame = pd.DataFrame(
        [record.as_dict() for record in [*bea_records, *rfa_records]]
    ).sort_values(
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

    estimate_years = {int(value) for value in config["analysis"]["salary_estimate_years"]}
    salary_estimates = frame[
        (frame["metric"] == RFA_METRIC)
        & (frame["geography"].isin(salary_peers))
        & (frame["year"].isin(estimate_years))
    ][
        [
            "geography",
            "year",
            "period",
            "value",
            "status",
            "is_revised",
            "source_release",
        ]
    ].rename(columns={"value": "nominal_salary", "source_release": "salary_release"})
    rpp_year = int(config["analysis"]["salary_rpp_year"])
    rpp = frame[
        (frame["metric"] == "regional_price_parity_all_items")
        & (frame["year"] == rpp_year)
        & (frame["geography"].isin(salary_peers))
    ][["geography", "value", "source_release"]].rename(
        columns={"value": "rpp", "source_release": "rpp_release"}
    )
    salary_comparison = salary_estimates.merge(rpp, on="geography", validate="many_to_one")
    expected_rows = len(salary_peers) * len(estimate_years)
    if len(salary_comparison) != expected_rows:
        raise ValueError("Teacher salary and RPP peer coverage is incomplete.")
    salary_comparison["rpp_year"] = rpp_year
    salary_comparison["purchasing_power_salary"] = salary_comparison.apply(
        lambda row: purchasing_power(float(row["nominal_salary"]), float(row["rpp"])),
        axis=1,
    )
    salary_comparison = salary_comparison.sort_values(["year", "geography"])
    salary_comparison.to_csv(
        curated / "teacher-salary-peer-comparison.csv",
        index=False,
        lineterminator="\n",
        float_format="%.3f",
    )

    lineage = {
        "sources": [
            {
                "source_id": source_id,
                "source_release": str(source["release"]),
                "source_sha256": manifest_entries[source_id]["source_sha256"],
                "snapshot_sha256": manifest_entries[source_id]["snapshot_sha256"],
                "rights_url": source["rights_url"],
                "approved_for_public_build": True,
            }
            for source_id, source in (("bea", bea_source), ("rfa", rfa_source))
        ]
    }
    with (curated / "lineage.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(lineage, indent=2) + "\n")
    render_all(
        frame,
        salary_comparison,
        figures,
        start_year=int(config["analysis"]["trend_start_year"]),
        latest_year=last_year,
        salary_latest_regional_actual_year=int(
            config["analysis"]["salary_latest_regional_actual_year"]
        ),
        salary_rpp_year=rpp_year,
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
