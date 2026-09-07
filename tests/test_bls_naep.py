from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.extract import (
    BLS_SERIES,
    extract_bls_oews_response,
    extract_naep_responses,
)

ROOT = Path(__file__).parents[1]


def test_bls_table_preserves_soc_codes_and_mean_median_labels() -> None:
    frame = pd.read_csv(ROOT / "data/curated/bls-oews-south-carolina-teacher-wages.csv")
    assert set(frame["soc_code"]) == {"25-2021", "25-2022", "25-2031"}
    assert set(frame["measure"]) == {"annual_mean_wage", "annual_median_wage"}
    values = {
        (row.soc_code, row.measure): row.value for row in frame.itertuples(index=False)
    }
    assert values[("25-2021", "annual_mean_wage")] == 62_210
    assert values[("25-2021", "annual_median_wage")] == 60_820
    assert values[("25-2022", "annual_mean_wage")] == 62_580
    assert values[("25-2022", "annual_median_wage")] == 60_810
    assert values[("25-2031", "annual_mean_wage")] == 65_340
    assert values[("25-2031", "annual_median_wage")] == 62_580


def test_bls_parser_rejects_missing_series() -> None:
    payload = {"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}
    with pytest.raises(ValueError, match="coverage changed"):
        extract_bls_oews_response(payload, source_release="test")
    assert len(BLS_SERIES) == 6


def test_naep_snapshot_has_all_48_records_and_south_carolina_ranks() -> None:
    frame = pd.read_csv(ROOT / "data/curated/naep-2024-regional-comparison.csv")
    assert len(frame) == 48
    assert frame["geography"].nunique() == 12
    assert frame["metric"].nunique() == 4
    south_carolina = frame[frame["geography"] == "South Carolina"].set_index("metric")
    expected = {
        "naep_grade_4_mathematics_at_or_above_proficient": (39.960, 5),
        "naep_grade_4_reading_at_or_above_proficient": (32.475, 3),
        "naep_grade_8_mathematics_at_or_above_proficient": (23.738, 5),
        "naep_grade_8_reading_at_or_above_proficient": (25.837, 7),
    }
    for metric, (value, rank) in expected.items():
        assert south_carolina.loc[metric, "value"] == pytest.approx(value, abs=0.001)
        assert south_carolina.loc[metric, "regional_rank"] == rank


def test_naep_parser_rejects_non_displayable_results() -> None:
    payload = {
        "status": 200,
        "result": [
            {
                "year": 2024,
                "grade": 4,
                "subject": "MAT",
                "stattype": "ALC:AP",
                "variable": "TOTAL",
                "jurisLabel": "South Carolina",
                "value": 40,
                "isStatDisplayable": 0,
                "errorFlag": 1,
            }
        ],
    }
    with pytest.raises(ValueError, match="not displayable"):
        extract_naep_responses([payload], source_release="test", peers={"South Carolina"})


def test_naep_caveats_are_published() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "may not be statistically significant" in text
    assert "NAEP Proficient is not the same as state-defined grade-level proficiency" in text
