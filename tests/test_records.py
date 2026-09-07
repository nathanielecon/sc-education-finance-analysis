import pytest

from sc_education_finance.records import Record, validate_records


def record(**changes: object) -> Record:
    values: dict[str, object] = {
        "source": "Synthetic source",
        "source_release": "2026",
        "geography": "Zone Alpha",
        "year": 2026,
        "metric": "synthetic_index",
        "value": 1.0,
        "unit": "index",
        "status": "actual",
    }
    values.update(changes)
    return Record(**values)  # type: ignore[arg-type]


def test_status_label_is_preserved() -> None:
    item = record(status="estimated")
    validate_records([item])
    assert item.status == "estimated"


def test_duplicate_rows_fail() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        validate_records([record(), record()])


def test_invalid_status_fails() -> None:
    with pytest.raises(ValueError, match="Invalid status"):
        validate_records([record(status="forecast")])


def test_incomplete_coverage_fails() -> None:
    with pytest.raises(ValueError, match="Incomplete peer-state coverage"):
        validate_records(
            [record()],
            required_geographies={"Zone Alpha", "Zone Beta"},
            required_years={2026},
        )


def test_non_finite_value_fails() -> None:
    with pytest.raises(ValueError, match="Malformed"):
        validate_records([record(value=float("nan"))])
