from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.extract import extract_bea_rpp


def write_source(path: Path) -> None:
    rows = []
    for line_code in range(1, 6):
        rows.extend(
            [
                {
                    "GeoName": "Zone Alpha",
                    "LineCode": line_code,
                    "2025": 80.0 + line_code,
                    "2026": 81.0 + line_code,
                },
                {
                    "GeoName": "Zone Beta",
                    "LineCode": line_code,
                    "2025": 90.0 + line_code,
                    "2026": 91.0 + line_code,
                },
            ]
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def test_extracts_each_named_rpp_series(tmp_path: Path) -> None:
    source = tmp_path / "synthetic.csv"
    write_source(source)
    records = extract_bea_rpp(
        source,
        source_release="test",
        peers={"Zone Alpha", "Zone Beta"},
        years=range(2025, 2027),
    )
    assert len(records) == 20
    assert {item.metric for item in records} == {
        "regional_price_parity_all_items",
        "regional_price_parity_goods",
        "regional_price_parity_services_housing",
        "regional_price_parity_services_utilities",
        "regional_price_parity_services_other",
    }


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
    with pytest.raises(ValueError, match="duplicate state-series rows"):
        extract_bea_rpp(
            source,
            source_release="test",
            peers={"Zone Alpha", "Zone Beta"},
            years=range(2025, 2027),
        )
