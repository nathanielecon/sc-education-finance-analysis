from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.extract import extract_bea_rpp


def write_source(path: Path) -> None:
    pd.DataFrame(
        [
            {"GeoName": "Zone Alpha", "LineCode": 1, "2025": "90.0", "2026": "91.0"},
            {"GeoName": "Zone Beta", "LineCode": 1, "2025": "99.0", "2026": "100.0"},
            {"GeoName": "Zone Alpha", "LineCode": 2, "2025": "50.0", "2026": "51.0"},
        ]
    ).to_csv(path, index=False)


def test_extracts_only_all_items_series(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    write_source(source)
    records = extract_bea_rpp(
        source,
        source_release="test",
        peers={"Zone Alpha", "Zone Beta"},
        years=range(2025, 2027),
    )
    assert len(records) == 4
    assert {item.value for item in records} == {90.0, 91.0, 99.0, 100.0}


def test_missing_column_fails(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    write_source(source)
    frame = pd.read_csv(source).drop(columns="2026")
    frame.to_csv(source, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        extract_bea_rpp(
            source,
            source_release="test",
            peers={"Zone Alpha", "Zone Beta"},
            years=range(2025, 2027),
        )


def test_duplicate_state_row_fails(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    write_source(source)
    frame = pd.read_csv(source)
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    frame.to_csv(source, index=False)
    with pytest.raises(ValueError, match="duplicate state rows"):
        extract_bea_rpp(
            source,
            source_release="test",
            peers={"Zone Alpha", "Zone Beta"},
            years=range(2025, 2027),
        )
