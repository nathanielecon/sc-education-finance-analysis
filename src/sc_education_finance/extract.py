from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import pandas as pd

from .adapters import read_pdf_text
from .metrics import normalize_state
from .records import Record, validate_records

RPP_METRICS = {
    1: "regional_price_parity_all_items",
    2: "regional_price_parity_goods",
    3: "regional_price_parity_services_housing",
    4: "regional_price_parity_services_utilities",
    5: "regional_price_parity_services_other",
}

RFA_SOURCE_NAME = "South Carolina Revenue and Fiscal Affairs Office teacher salary survey"
RFA_METRIC = "average_teacher_salary"
RFA_UNIT = "current dollars"
RFA_YEARS = list(range(2020, 2028))
RFA_ROW_NAMES = (
    "Alabama",
    "Arkansas",
    "Florida",
    "Georgia",
    "Kentucky",
    "Louisiana",
    "Mississippi",
    "N. Carolina",
    "Tennessee",
    "Virginia",
    "W. Virginia",
)

BLS_SOURCE_NAME = "U.S. Bureau of Labor Statistics Occupational Employment and Wage Statistics"
BLS_OCCUPATIONS = {
    "252021": "Elementary School Teachers, Except Special Education",
    "252022": "Middle School Teachers, Except Special and Career/Technical Education",
    "252031": "Secondary School Teachers, Except Special and Career/Technical Education",
}
BLS_MEASURES = {
    "04": "annual_mean_wage",
    "13": "annual_median_wage",
}
BLS_SERIES = {
    f"OEUS4500000000000{occupation}{measure}": (occupation, metric)
    for occupation in BLS_OCCUPATIONS
    for measure, metric in BLS_MEASURES.items()
}

NAEP_SOURCE_NAME = "National Assessment of Educational Progress Data Service"
NAEP_METRICS = {
    (4, "MAT"): "naep_grade_4_mathematics_at_or_above_proficient",
    (4, "RED"): "naep_grade_4_reading_at_or_above_proficient",
    (8, "MAT"): "naep_grade_8_mathematics_at_or_above_proficient",
    (8, "RED"): "naep_grade_8_reading_at_or_above_proficient",
}

SCENARIO_METHOD = (
    "NEA FY 2025-26 estimate + enacted FY 2026-27 statewide schedule increase"
)
SCENARIO_INPUT_SOURCE_IDS = "nea_2026_salary_estimate;sc_fy2026_27_schedule_increase"
SCENARIO_ASSUMPTIONS = (
    "Adds the enacted $2,000 increase for every state minimum salary schedule cell "
    "to the NEA estimate. Teacher composition, experience, district supplements, and "
    "turnover are held constant."
)


def _fiscal_period(year: int) -> str:
    return f"FY {year - 1}-{str(year)[-2:]}"


def _rfa_cells(line: str) -> list[tuple[float, bool]]:
    return [
        (float(value.replace(",", "")), revised == "r")
        for value, revised in re.findall(r"(\d{1,3}(?:,\d{3})+)(?:\s+(r))?", line)
    ]


def _find_line(text: str, prefix: str) -> str:
    matches = [line.strip() for line in text.splitlines() if line.strip().startswith(prefix)]
    if len(matches) != 1:
        raise ValueError(f"RFA source layout changed for row {prefix!r}.")
    return matches[0]


def extract_rfa_salary_pdf(
    path: Path, *, source_release: str, peer_states: set[str]
) -> list[Record]:
    """Extract selected facts from the RFA teacher salary survey."""
    text = read_pdf_text(path)
    required_markers = (
        "FY 19-20 FY 20-21 FY 21-22 FY 22-23 FY 23-24 FY 24-25 FY 25-26 FY 26-27",
        "r - Revised since previous estimate.",
        "Updated 11/19/2025 to include SC actual salary figure for FY 2024-25",
    )
    missing_markers = [marker for marker in required_markers if marker not in text]
    if missing_markers:
        raise ValueError(f"RFA source layout changed; missing markers: {missing_markers}")

    records: list[Record] = []
    sc_cells = _rfa_cells(_find_line(text, "South Carolina Actual"))
    if len(sc_cells) != 6:
        raise ValueError("RFA South Carolina row must contain six actual values.")
    for year, (value, revised) in zip(range(2020, 2026), sc_cells, strict=True):
        records.append(
            Record(
                source=RFA_SOURCE_NAME,
                source_release=source_release,
                geography="South Carolina",
                year=year,
                period=_fiscal_period(year),
                metric=RFA_METRIC,
                value=value,
                unit=RFA_UNIT,
                status="actual",
                is_revised=revised,
                rpp_year=None,
            )
        )

    average_cells = _rfa_cells(_find_line(text, "SE Avg. from Survey"))
    if len(average_cells) != 8:
        raise ValueError("RFA Southeastern average row must contain eight values.")
    for year, (value, revised) in zip(RFA_YEARS, average_cells, strict=True):
        records.append(
            Record(
                source=RFA_SOURCE_NAME,
                source_release=source_release,
                geography="Southeastern average",
                year=year,
                period=_fiscal_period(year),
                metric=RFA_METRIC,
                value=value,
                unit=RFA_UNIT,
                status="estimated" if year >= 2025 else "actual",
                is_revised=revised,
                rpp_year=None,
            )
        )

    found_peers: set[str] = set()
    for row_name in RFA_ROW_NAMES:
        geography = normalize_state(row_name)
        cells = _rfa_cells(_find_line(text, row_name))
        if len(cells) != 8:
            raise ValueError(f"RFA row for {geography} must contain eight values.")
        found_peers.add(geography)
        for year, (value, revised) in zip((2025, 2026, 2027), cells[-3:], strict=True):
            records.append(
                Record(
                    source=RFA_SOURCE_NAME,
                    source_release=source_release,
                    geography=geography,
                    year=year,
                    period=_fiscal_period(year),
                    metric=RFA_METRIC,
                    value=value,
                    unit=RFA_UNIT,
                    status="estimated",
                    is_revised=revised,
                    rpp_year=None,
                )
            )
    if found_peers != peer_states:
        raise ValueError(
            f"RFA peer-state coverage changed: {sorted(peer_states - found_peers)}"
        )
    validate_records(records)
    return records


def load_rfa_salary_snapshot(
    path: Path, *, source_release: str, peer_states: set[str]
) -> list[Record]:
    """Validate the committed snapshot of selected RFA facts."""
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required_columns = [
        "source",
        "source_release",
        "geography",
        "year",
        "period",
        "metric",
        "value",
        "unit",
        "status",
        "is_revised",
        "rpp_year",
    ]
    optional_columns = ["method", "input_source_ids", "assumptions"]
    if frame.columns.tolist() not in (
        required_columns,
        [*required_columns, *optional_columns],
    ):
        raise ValueError("The selected RFA snapshot schema changed.")

    records: list[Record] = []
    for row in frame.to_dict(orient="records"):
        if row["source"] != RFA_SOURCE_NAME or row["source_release"] != source_release:
            raise ValueError("The selected RFA snapshot has invalid source metadata.")
        if row["metric"] != RFA_METRIC or row["unit"] != RFA_UNIT:
            raise ValueError("The selected RFA snapshot has an unexpected metric or unit.")
        revised_value = row["is_revised"].strip().lower()
        if revised_value not in {"true", "false"}:
            raise ValueError("The selected RFA snapshot has an invalid revision flag.")
        records.append(
            Record(
                source=row["source"],
                source_release=row["source_release"],
                geography=normalize_state(row["geography"]),
                year=int(row["year"]),
                period=row["period"],
                metric=row["metric"],
                value=float(row["value"]),
                unit=row["unit"],
                status=row["status"],
                is_revised=revised_value == "true",
                rpp_year=int(row["rpp_year"]) if row["rpp_year"] else None,
                method=row.get("method") or None,
                input_source_ids=row.get("input_source_ids") or None,
                assumptions=row.get("assumptions") or None,
            )
        )

    validate_records(records)
    expected_keys = {
        *(('South Carolina', year) for year in range(2020, 2026)),
        *(('Southeastern average', year) for year in RFA_YEARS),
        *((state, year) for state in peer_states for year in (2025, 2026, 2027)),
    }
    found_keys = {(record.geography, record.year) for record in records}
    if found_keys != expected_keys:
        missing = sorted(expected_keys - found_keys)
        extra = sorted(found_keys - expected_keys)
        raise ValueError(f"RFA selected-fact coverage changed; missing={missing}, extra={extra}")
    return records


def _record_from_row(row: Mapping[str, str]) -> Record:
    revised_value = row["is_revised"].strip().lower()
    if revised_value not in {"true", "false"}:
        raise ValueError("The selected snapshot has an invalid revision flag.")
    return Record(
        source=row["source"],
        source_release=row["source_release"],
        geography=normalize_state(row["geography"]),
        year=int(row["year"]),
        period=row["period"],
        metric=row["metric"],
        value=float(row["value"]),
        unit=row["unit"],
        status=row["status"],
        is_revised=revised_value == "true",
        rpp_year=int(row["rpp_year"]) if row["rpp_year"] else None,
        method=row.get("method") or None,
        input_source_ids=row.get("input_source_ids") or None,
        assumptions=row.get("assumptions") or None,
    )


def load_selected_records(path: Path) -> list[Record]:
    """Load a small, attributed snapshot that uses the normalized record schema."""
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    required = {
        "source",
        "source_release",
        "geography",
        "year",
        "period",
        "metric",
        "value",
        "unit",
        "status",
        "is_revised",
        "rpp_year",
    }
    if not required.issubset(frame.columns):
        raise ValueError(f"Selected snapshot is missing columns: {sorted(required - set(frame.columns))}")
    records = [
        _record_from_row(cast(Mapping[str, str], row))
        for row in frame.to_dict(orient="records")
    ]
    validate_records(records)
    return records


def derive_south_carolina_salary_scenario(inputs: list[Record]) -> Record:
    """Calculate the FY 2026-27 schedule-only scenario from its two inputs."""
    estimate = [
        record
        for record in inputs
        if record.geography == "South Carolina"
        and record.year == 2026
        and record.metric == RFA_METRIC
        and record.status == "estimated"
    ]
    increase = [
        record
        for record in inputs
        if record.geography == "South Carolina"
        and record.year == 2027
        and record.metric == "state_minimum_teacher_salary_schedule_cell_increase"
    ]
    if len(estimate) != 1 or len(increase) != 1:
        raise ValueError("The salary scenario requires one NEA estimate and one schedule increase.")
    return Record(
        source="Project calculation from attributed source inputs",
        source_release="FY 2026-27",
        geography="South Carolina",
        year=2027,
        period="FY 2026-27",
        metric=RFA_METRIC,
        value=estimate[0].value + increase[0].value,
        unit="current dollars",
        status="modeled_scenario",
        is_revised=False,
        rpp_year=None,
        method=SCENARIO_METHOD,
        input_source_ids=SCENARIO_INPUT_SOURCE_IDS,
        assumptions=SCENARIO_ASSUMPTIONS,
    )


def extract_bls_oews_response(payload: Mapping[str, Any], *, source_release: str) -> list[Record]:
    """Normalize six South Carolina teacher-wage series from the BLS API."""
    results = payload.get("Results")
    if payload.get("status") != "REQUEST_SUCCEEDED" or not isinstance(results, Mapping):
        raise ValueError("The BLS response was unsuccessful or malformed.")
    series = results.get("series")
    if not isinstance(series, list):
        raise ValueError("The BLS response lacks a series array.")
    indexed = {str(item.get("seriesID")): item for item in series if isinstance(item, Mapping)}
    if set(indexed) != set(BLS_SERIES):
        raise ValueError("BLS teacher-wage series coverage changed.")

    records: list[Record] = []
    for series_id, (occupation, measure) in BLS_SERIES.items():
        points = indexed[series_id].get("data")
        if not isinstance(points, list) or len(points) != 1 or not isinstance(points[0], Mapping):
            raise ValueError(f"BLS series {series_id} must contain one annual point.")
        point = points[0]
        if point.get("year") != "2025" or point.get("periodName") != "Annual":
            raise ValueError(f"BLS series {series_id} has an unexpected reference period.")
        records.append(
            Record(
                source=BLS_SOURCE_NAME,
                source_release=source_release,
                geography="South Carolina",
                year=2025,
                period="May 2025",
                metric=f"oews_{occupation}_{measure}",
                value=float(str(point["value"])),
                unit="current dollars per year",
                status="estimated",
                is_revised=False,
                rpp_year=None,
            )
        )
    validate_records(records)
    return records


def extract_naep_responses(
    payloads: list[Mapping[str, Any]], *, source_release: str, peers: set[str]
) -> list[Record]:
    """Normalize aggregate 2024 NAEP proficiency results for the peer states."""
    records: list[Record] = []
    for payload in payloads:
        if payload.get("status") != 200 or not isinstance(payload.get("result"), list):
            raise ValueError("A NAEP response was unsuccessful or malformed.")
        for item in payload["result"]:
            if not isinstance(item, Mapping):
                raise ValueError("A NAEP result row is malformed.")
            key = (int(item["grade"]), str(item["subject"]))
            if key not in NAEP_METRICS:
                raise ValueError(f"Unexpected NAEP grade-subject pair: {key}")
            if (
                item.get("year") != 2024
                or item.get("stattype") != "ALC:AP"
                or item.get("variable") != "TOTAL"
                or item.get("isStatDisplayable") != 1
                or item.get("errorFlag") != 0
            ):
                raise ValueError("NAEP result metadata changed or a value is not displayable.")
            records.append(
                Record(
                    source=NAEP_SOURCE_NAME,
                    source_release=source_release,
                    geography=normalize_state(str(item["jurisLabel"])),
                    year=2024,
                    period="2024 assessment",
                    metric=NAEP_METRICS[key],
                    value=float(item["value"]),
                    unit="percent at or above NAEP Proficient",
                    status="actual",
                    is_revised=False,
                    rpp_year=None,
                )
            )
    validate_records(records)
    expected = {(state, metric) for state in peers for metric in NAEP_METRICS.values()}
    observed = {(record.geography, record.metric) for record in records}
    if observed != expected:
        raise ValueError(
            f"NAEP peer coverage changed; missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}"
        )
    return records


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
                        period=str(year),
                        metric=metric,
                        value=value,
                        unit="index (United States = 100)",
                        status="actual",
                        is_revised=False,
                        rpp_year=year,
                    )
                )
    validate_records(
        records, required_geographies=peers, required_years=set(years)
    )
    return records
