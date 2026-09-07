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
    snapshot = ROOT / "data/source/bea-rpp-state-2008-2024.csv"
    manifest = json.loads((ROOT / "data/source/source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["sources"][0]["sha256"] == sha256(snapshot)


def test_public_registry_approves_only_bea() -> None:
    assert approved_source_ids(load_config(ROOT)) == ["bea"]


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
        "policy as code",
    ):
        assert term in text
    assert "agentic AI project" not in text.lower()


def test_public_build_contains_no_excluded_source_material() -> None:
    blocked_tokens = (
        "national education association",
        "south carolina department of education",
        "revenue and fiscal affairs",
        "nea.org",
        "ed.sc.gov",
        "rfa.sc.gov",
        "dropbox.com",
        "64" + "050",
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
