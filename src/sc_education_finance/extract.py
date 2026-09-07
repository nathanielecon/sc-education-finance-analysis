from __future__ import annotations

from pathlib import Path

import pandas as pd

from .metrics import normalize_state
from .records import Record, validate_records

RPP_METRICS = {
    1: "regional_price_parity_all_items",
    2: "regional_price_parity_goods",
    3: "regional_price_parity_services_housing",
    4: "regional_price_parity_services_utilities",
    5: "regional_price_parity_services_other",
}


def extract_bea_rpp(
    path: Path, *, source_release: str, peers: set[str], years: range
) -> list[Record]:
    """Normalize the approved BEA state RPP snapshot."""
    frame = pd.read_csv(path, dtype={"GeoName": "string"})
    year_columns = {str(year) for year in years}
    required = {"GeoName", "LineCode", *year_columns}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"BEA source is missing columns: {sorted(missing)}")

    frame["GeoName"] = frame["GeoName"].fillna("").astype(str).map(normalize_state)
    peer_rows = frame[
        frame["LineCode"].isin(RPP_METRICS) & frame["GeoName"].isin(peers)
    ].copy()
    duplicates = peer_rows.duplicated(subset=["GeoName", "LineCode"], keep=False)
    if duplicates.any():
        keys = sorted(
            (str(row.GeoName), int(float(str(row.LineCode))))
            for row in peer_rows.loc[duplicates].itertuples()
        )
        raise ValueError(f"BEA source has duplicate state-series rows: {keys}")

    expected_keys = {(state, line_code) for state in peers for line_code in RPP_METRICS}
    found_keys = {
        (str(row.GeoName), int(float(str(row.LineCode)))) for row in peer_rows.itertuples()
    }
    if expected_keys - found_keys:
        raise ValueError(f"BEA series coverage is incomplete: {sorted(expected_keys - found_keys)}")

    records: list[Record] = []
    indexed = peer_rows.set_index(["GeoName", "LineCode"])
    for geography in sorted(peers):
        for line_code, metric in RPP_METRICS.items():
            for year in years:
                raw_value = indexed.at[(geography, line_code), str(year)]
                try:
                    value = float(str(raw_value))
                except ValueError as error:
                    raise ValueError(
                        f"Malformed BEA value for {geography}, series {line_code}, {year}: "
                        f"{raw_value!r}"
                    ) from error
                records.append(
                    Record(
                        source="BEA regional price parities",
                        source_release=source_release,
                        geography=geography,
                        year=year,
                        metric=metric,
                        value=value,
                        unit="index (United States = 100)",
                        status="actual",
                    )
                )
    validate_records(
        records, required_geographies=peers, required_years=set(years)
    )
    return records
