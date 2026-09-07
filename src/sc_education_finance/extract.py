from __future__ import annotations

from pathlib import Path

import pandas as pd

from .metrics import normalize_state
from .records import Record, validate_records


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
    peer_rows = frame[(frame["LineCode"] == 1) & frame["GeoName"].isin(peers)].copy()
    duplicates = peer_rows["GeoName"].duplicated(keep=False)
    if duplicates.any():
        names = sorted(peer_rows.loc[duplicates, "GeoName"].astype(str).unique())
        raise ValueError(f"BEA source has duplicate state rows: {names}")

    found = set(peer_rows["GeoName"].dropna().astype(str))
    if peers - found:
        raise ValueError(f"BEA peer coverage is incomplete: {sorted(peers - found)}")

    records: list[Record] = []
    indexed = peer_rows.set_index("GeoName")
    for geography in sorted(peers):
        for year in years:
            raw_value = indexed.at[geography, str(year)]
            try:
                value = float(str(raw_value))
            except ValueError as error:
                raise ValueError(
                    f"Malformed BEA value for {geography}, {year}: {raw_value!r}"
                ) from error
            records.append(
                Record(
                    source="BEA regional price parities",
                    source_release=source_release,
                    geography=geography,
                    year=year,
                    metric="regional_price_parity",
                    value=value,
                    unit="index (United States = 100)",
                    status="actual",
                )
            )
    validate_records(
        records, required_geographies=peers, required_years=set(years)
    )
    return records
