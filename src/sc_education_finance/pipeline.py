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
from .extract import (
    BLS_OCCUPATIONS,
    RFA_METRIC,
    derive_south_carolina_salary_scenario,
    extract_bea_rpp,
    load_rfa_salary_snapshot,
    load_selected_records,
)
from .metrics import competition_ranks, purchasing_power
from .rights import assert_source_use_allowed

OUTPUTS = [
    "data/curated/observations.csv",
    "data/curated/south-carolina-peer-comparison.csv",
    "data/curated/teacher-salary-peer-comparison.csv",
    "data/curated/latest-available-teacher-salaries.csv",
    "data/curated/bls-oews-south-carolina-teacher-wages.csv",
    "data/curated/naep-2024-regional-comparison.csv",
    "data/curated/lineage.json",
    "docs/assets/figures/southeastern-rpp-trends.svg",
    "docs/assets/figures/southeastern-rpp-trends.png",
    "docs/assets/figures/south-carolina-peer-rpp.svg",
    "docs/assets/figures/south-carolina-peer-rpp.png",
    "docs/assets/figures/salary-trends.svg",
    "docs/assets/figures/salary-trends.png",
    "docs/assets/figures/salary-comparison-side-by-side.svg",
    "docs/assets/figures/salary-comparison-side-by-side.png",
    "docs/assets/figures/naep-regional-comparison.svg",
    "docs/assets/figures/naep-regional-comparison.png",
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
        acquisition = str(indexed[source_id].get("acquisition", "download"))
        source_hash = str(indexed[source_id].get("source_sha256", ""))
        if acquisition == "download" and len(source_hash) != 64:
            raise ValueError(f"The {source_id} source hash is missing or malformed.")
        if acquisition == "manual_fact_verification" and source_hash != "not-downloaded":
            raise ValueError(f"The {source_id} manual source must remain undownloaded.")
    return indexed


def select_latest_salary_rows(frame: pd.DataFrame, peers: set[str]) -> pd.DataFrame:
    """Select the latest actual for each state, then use the latest RFA estimate."""
    rows: list[pd.Series[Any]] = []
    salary = frame[
        (frame["metric"] == RFA_METRIC)
        & (frame["geography"].isin(peers))
        & (frame["status"].isin(["actual", "estimated"]))
    ]
    for geography in sorted(peers):
        state = salary[salary["geography"] == geography]
        actual = state[state["status"] == "actual"]
        eligible = actual if not actual.empty else state[state["status"] == "estimated"]
        if eligible.empty:
            raise ValueError(f"No compatible salary observation is available for {geography}.")
        rows.append(eligible.sort_values("year").iloc[-1])
    result = pd.DataFrame(rows).rename(columns={"value": "salary"})
    result["selection_basis"] = result["status"].map(
        {"actual": "latest official actual", "estimated": "RFA estimate fallback"}
    )
    return result[
        [
            "geography",
            "year",
            "period",
            "salary",
            "status",
            "is_revised",
            "source",
            "source_release",
            "selection_basis",
        ]
    ].sort_values("geography")


def assert_salary_table_rankable(frame: pd.DataFrame) -> None:
    """Reject rankings when period, status, or source are not matched."""
    for column in ("year", "status", "source"):
        if frame[column].nunique(dropna=False) != 1:
            raise ValueError(f"Mixed salary {column} values cannot be ranked.")


def build(root: Path, destination: Path | None = None) -> list[Path]:
    """Validate sources, normalize data, and render the committed outputs."""
    config = load_config(root)
    bea_source = assert_source_use_allowed(config, "bea", use="factual_extraction")
    assert_source_use_allowed(config, "bea", use="derivative_visualization")
    rfa_source = assert_source_use_allowed(config, "rfa", use="factual_extraction")
    assert_source_use_allowed(config, "rfa", use="derivative_visualization")
    bls_source = assert_source_use_allowed(config, "bls", use="factual_extraction")
    naep_source = assert_source_use_allowed(config, "naep", use="factual_extraction")
    assert_source_use_allowed(config, "naep", use="derivative_visualization")
    nea_source = assert_source_use_allowed(config, "nea", use="factual_extraction")
    assert_source_use_allowed(config, "nea", use="derivative_visualization")
    budget_source = assert_source_use_allowed(config, "sc_budget", use="factual_extraction")
    assert_source_use_allowed(config, "sc_budget", use="derivative_visualization")
    schedule_source = assert_source_use_allowed(
        config, "scde_salary_schedule", use="factual_extraction"
    )
    source_dir = resolve_path(root, config["paths"]["source"])
    snapshots = {
        "bea": source_dir / str(bea_source["snapshot"]),
        "rfa": source_dir / str(rfa_source["snapshot"]),
        "bls": source_dir / str(bls_source["snapshot"]),
        "naep": source_dir / str(naep_source["snapshot"]),
        "nea": source_dir / str(nea_source["snapshot"]),
        "sc_budget": source_dir / str(budget_source["snapshot"]),
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
    bls_records = load_selected_records(snapshots["bls"])
    naep_records = load_selected_records(snapshots["naep"])
    if len(bls_records) != 6:
        raise ValueError("The BLS selected-fact snapshot must contain six wage observations.")
    if len(naep_records) != 48:
        raise ValueError("The NAEP selected-fact snapshot must contain 48 observations.")
    nea_inputs = load_selected_records(snapshots["nea"])
    budget_inputs = load_selected_records(snapshots["sc_budget"])
    scenario = derive_south_carolina_salary_scenario([*nea_inputs, *budget_inputs])
    frame = pd.DataFrame(
        [
            record.as_dict()
            for record in [
                *bea_records,
                *rfa_records,
                *bls_records,
                *naep_records,
                *nea_inputs,
                *budget_inputs,
                scenario,
            ]
        ]
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

    comparison_year = int(config["analysis"]["salary_comparison_year"])
    comparison_geographies = salary_peers | {"South Carolina"}
    salary_values = frame[
        (frame["metric"] == RFA_METRIC)
        & (frame["geography"].isin(comparison_geographies))
        & (frame["year"] == comparison_year)
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
        & (frame["geography"].isin(comparison_geographies))
    ][["geography", "value", "source_release"]].rename(
        columns={"value": "rpp", "source_release": "rpp_release"}
    )
    salary_comparison = salary_values.merge(rpp, on="geography", validate="one_to_one")
    expected_rows = len(comparison_geographies)
    if len(salary_comparison) != expected_rows:
        raise ValueError("Teacher salary and RPP peer coverage is incomplete.")
    salary_comparison["rpp_year"] = rpp_year
    salary_comparison["purchasing_power_salary"] = salary_comparison.apply(
        lambda row: purchasing_power(float(row["nominal_salary"]), float(row["rpp"])),
        axis=1,
    )
    salary_comparison["nominal_rank"] = competition_ranks(
        salary_comparison["nominal_salary"].tolist()
    )
    salary_comparison["purchasing_power_rank"] = competition_ranks(
        salary_comparison["purchasing_power_salary"].tolist()
    )
    salary_comparison = salary_comparison.sort_values(["year", "geography"])
    salary_comparison.to_csv(
        curated / "teacher-salary-peer-comparison.csv",
        index=False,
        lineterminator="\n",
        float_format="%.3f",
    )

    latest_salary = select_latest_salary_rows(frame, comparison_geographies)
    latest_salary.to_csv(
        curated / "latest-available-teacher-salaries.csv",
        index=False,
        lineterminator="\n",
        float_format="%.3f",
    )

    bls_table = frame[frame["metric"].str.startswith("oews_")].copy()
    bls_table["soc_code"] = bls_table["metric"].str.extract(r"oews_(\d{6})_")[0].map(
        lambda value: f"{value[:2]}-{value[2:]}"
    )
    bls_table["occupation"] = bls_table["soc_code"].str.replace("-", "").map(
        BLS_OCCUPATIONS
    )
    bls_table["measure"] = bls_table["metric"].str.replace(
        r"oews_\d{6}_", "", regex=True
    )
    bls_table = bls_table[
        ["soc_code", "occupation", "period", "measure", "value", "unit", "source_release"]
    ].sort_values(["soc_code", "measure"])
    bls_table.to_csv(
        curated / "bls-oews-south-carolina-teacher-wages.csv",
        index=False,
        lineterminator="\n",
        float_format="%.3f",
    )

    naep_comparison = frame[frame["metric"].str.startswith("naep_")].copy()
    naep_comparison["regional_rank"] = naep_comparison.groupby("metric")["value"].rank(
        method="min", ascending=False
    ).astype(int)
    naep_comparison = naep_comparison.sort_values(["geography", "metric"])
    naep_comparison.to_csv(
        curated / "naep-2024-regional-comparison.csv",
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
            for source_id, source in (
                ("bea", bea_source),
                ("rfa", rfa_source),
                ("bls", bls_source),
                ("naep", naep_source),
                ("nea", nea_source),
                ("sc_budget", budget_source),
            )
        ]
    }
    lineage["supporting_sources"] = [
        {
            "source_id": "scde_salary_schedule",
            "source_release": str(schedule_source["release"]),
            "rights_url": schedule_source["rights_url"],
            "approved_for_public_build": True,
            "use": "corroborating link only",
        }
    ]
    with (curated / "lineage.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(lineage, indent=2) + "\n")
    render_all(
        frame,
        salary_comparison,
        naep_comparison,
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
