import json
from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.config import load_config
from sc_education_finance.download import sha256
from sc_education_finance.rights import approved_source_ids

ROOT = Path(__file__).parents[1]


def test_south_carolina_2024_spot_check() -> None:
    frame = pd.read_csv(ROOT / "data/curated/observations.csv")
    row = frame[
        (frame["geography"] == "South Carolina")
        & (frame["year"] == 2024)
        & (frame["metric"] == "regional_price_parity_all_items")
    ]
    assert len(row) == 1
    assert row.iloc[0]["value"] == pytest.approx(93.749)
    assert row.iloc[0]["status"] == "actual"


def test_south_carolina_2024_services_other_spot_check() -> None:
    frame = pd.read_csv(ROOT / "data/curated/observations.csv")
    row = frame[
        (frame["geography"] == "South Carolina")
        & (frame["year"] == 2024)
        & (frame["metric"] == "regional_price_parity_services_other")
    ]
    assert len(row) == 1
    assert row.iloc[0]["value"] == pytest.approx(98.284)
    assert row.iloc[0]["status"] == "actual"


def test_source_snapshot_matches_manifest() -> None:
    manifest = json.loads((ROOT / "data/source/source-manifest.json").read_text(encoding="utf-8"))
    entries = {entry["source_id"]: entry for entry in manifest["sources"]}
    snapshots = {
        "bea": ROOT / "data/source/bea-rpp-state-2008-2024.csv",
        "rfa": ROOT / "data/source/rfa-teacher-salary-selected.csv",
    }
    assert set(entries) == set(snapshots)
    for source_id, snapshot in snapshots.items():
        assert entries[source_id]["snapshot_sha256"] == sha256(snapshot)
        assert len(entries[source_id]["source_sha256"]) == 64
    assert (
        entries["rfa"]["source_sha256"]
        == "0f8a0e37672f8e9b9c7f412b9573134a1bb43975eb231bfec2c4607a5a5feee9"
    )


def test_public_registry_approves_bea_and_limited_rfa_use() -> None:
    config = load_config(ROOT)
    assert approved_source_ids(config, use="factual_extraction") == ["bea", "rfa"]
    assert approved_source_ids(config, use="raw_redistribution") == ["bea"]


def test_readme_has_supported_engineering_terms() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for term in (
        "Python",
        "ETL",
        "data pipeline",
        "schema validation",
        "test automation",
        "CI/CD",
        "GitHub Actions",
    ):
        assert term in text
    for path in (ROOT / "README.md", ROOT / "docs/findings.md"):
        lowered = path.read_text(encoding="utf-8").lower()
        assert "agentic ai" not in lowered
        assert "recruiter-facing" not in lowered
        assert "recruiter facing" not in lowered
        assert "case study" not in lowered


@pytest.mark.parametrize(
    ("geography", "year", "value", "status"),
    [
        ("South Carolina", 2025, 64_050, "actual"),
        ("Southeastern average", 2025, 61_749, "estimated"),
        ("Southeastern average", 2026, 63_085, "estimated"),
        ("Southeastern average", 2027, 65_545, "estimated"),
        ("Virginia", 2027, 78_987, "estimated"),
        ("Mississippi", 2027, 56_314, "estimated"),
    ],
)
def test_rfa_salary_spot_checks(
    geography: str, year: int, value: int, status: str
) -> None:
    frame = pd.read_csv(ROOT / "data/curated/observations.csv")
    row = frame[
        (frame["geography"] == geography)
        & (frame["year"] == year)
        & (frame["metric"] == "average_teacher_salary")
    ]
    assert len(row) == 1
    assert row.iloc[0]["value"] == value
    assert row.iloc[0]["status"] == status


def test_salary_comparisons_include_south_carolina_and_use_2024_rpp() -> None:
    frame = pd.read_csv(ROOT / "data/curated/teacher-salary-peer-comparison.csv")
    assert set(frame["year"]) == {2025}
    assert set(frame["geography"]) == {
        "Alabama",
        "Arkansas",
        "Florida",
        "Georgia",
        "Kentucky",
        "Louisiana",
        "Mississippi",
        "North Carolina",
        "South Carolina",
        "Tennessee",
        "Virginia",
        "West Virginia",
    }
    assert set(frame["rpp_year"]) == {2024}
    row = frame[frame["geography"] == "South Carolina"].iloc[0]
    assert row["nominal_salary"] == 64_050
    assert row["status"] == "actual"
    assert row["purchasing_power_salary"] == pytest.approx(
        row["nominal_salary"] / (row["rpp"] / 100), abs=0.001
    )


def test_south_carolina_salary_ranks_change_after_rpp_adjustment() -> None:
    frame = pd.read_csv(ROOT / "data/curated/teacher-salary-peer-comparison.csv")
    nominal = frame.sort_values("nominal_salary", ascending=False).reset_index(drop=True)
    adjusted = frame.sort_values(
        "purchasing_power_salary", ascending=False
    ).reset_index(drop=True)
    assert nominal.index[nominal["geography"] == "South Carolina"].item() + 1 == 3
    assert adjusted.index[adjusted["geography"] == "South Carolina"].item() + 1 == 7
    sc_adjusted = adjusted.loc[
        adjusted["geography"] == "South Carolina", "purchasing_power_salary"
    ].item()
    assert sc_adjusted == pytest.approx(68_320.729, abs=0.001)


def test_salary_figures_use_title_case_and_match_years() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "# South Carolina Teacher Salary and Regional Cost Analysis" in readme
    assert "docs/assets/figures/nominal-salary-comparison.svg" in readme
    assert "docs/assets/figures/adjusted-salary-comparison.svg" in readme
    assert "peer-salary-estimates.svg" not in readme

    nominal_svg = (
        ROOT / "docs/assets/figures/nominal-salary-comparison.svg"
    ).read_text(encoding="utf-8")
    adjusted_svg = (
        ROOT / "docs/assets/figures/adjusted-salary-comparison.svg"
    ).read_text(encoding="utf-8")
    assert "Average Teacher Salaries, FY 2024-25" in nominal_svg
    assert "Teacher Salaries After Regional Price Adjustment, FY 2024-25" in adjusted_svg
    for svg in (nominal_svg, adjusted_svg):
        assert "South Carolina" in svg
        assert "$64,050" in svg or "$68,321" in svg
        assert "RFA reports South Carolina as actual." in svg
        assert "RFA marks peer-state values as revised estimates." in svg


def test_public_build_contains_no_excluded_source_material() -> None:
    blocked_tokens = (
        "national education association",
        "south carolina department of education",
        "nea.org",
        "ed.sc.gov",
        "dropbox.com",
        "67" + "107",
        "14" + "944",
        "15" + "888",
    )
    for folder in (ROOT / "src", ROOT / "data/curated", ROOT / "docs/assets/figures"):
        for path in folder.rglob("*"):
            if path.is_file():
                text = path.read_bytes().decode("utf-8", errors="ignore").lower()
                assert all(token not in text for token in blocked_tokens), path


def test_production_code_has_no_personal_paths_or_credentials() -> None:
    forbidden = (
        "c:" + "\\users\\",
        "pdf" + ".co",
        "api" + "_key",
        "api" + "key",
    )
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert all(token not in text for token in forbidden), path
