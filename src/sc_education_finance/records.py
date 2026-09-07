from __future__ import annotations

import math
from dataclasses import asdict, dataclass

VALID_STATUSES = {"actual", "revised", "estimated"}


@dataclass(frozen=True, slots=True)
class Record:
    source: str
    source_release: str
    geography: str
    year: int
    metric: str
    value: float
    unit: str
    status: str

    def as_dict(self) -> dict[str, str | float | int]:
        return asdict(self)


def validate_records(
    records: list[Record],
    *,
    required_geographies: set[str] | None = None,
    required_years: set[int] | None = None,
) -> None:
    """Reject empty, malformed, duplicate, or incomplete normalized records."""
    if not records:
        raise ValueError("No records were produced.")
    keys: set[tuple[str, int, str]] = set()
    for record in records:
        if record.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {record.status}")
        if not math.isfinite(record.value):
            raise ValueError(f"Malformed value for {record.metric}")
        key = (record.geography, record.year, record.metric)
        if key in keys:
            raise ValueError(f"Duplicate geography-year-metric row: {key}")
        keys.add(key)
    if required_geographies and required_years:
        observed = {(record.geography, record.year) for record in records}
        expected = {
            (geography, year)
            for geography in required_geographies
            for year in required_years
        }
        missing = expected - observed
        if missing:
            raise ValueError(f"Incomplete peer-state coverage: {sorted(missing)}")
