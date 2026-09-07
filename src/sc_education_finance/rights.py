from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_FIELDS = {
    "publisher",
    "landing_url",
    "rights_basis",
    "rights_url",
    "redistribution_permitted",
    "derivative_visualizations_permitted",
    "approved_for_public_build",
    "reviewed_on",
}


def validate_source_registry(config: Mapping[str, Any]) -> None:
    """Validate every source decision before acquisition or publication."""
    sources = config.get("sources")
    if not isinstance(sources, Mapping) or not sources:
        raise ValueError("The source-rights registry is missing or empty.")
    for source_id, raw_decision in sources.items():
        if not isinstance(raw_decision, Mapping):
            raise ValueError(f"The rights decision for {source_id!r} is malformed.")
        missing = REQUIRED_FIELDS - set(raw_decision)
        if missing:
            raise ValueError(
                f"The rights decision for {source_id!r} is missing: {sorted(missing)}"
            )
        for field in ("landing_url", "rights_url"):
            if not str(raw_decision[field]).startswith("https://"):
                raise ValueError(f"The {field} for {source_id!r} must be an HTTPS URL.")
        for field in (
            "redistribution_permitted",
            "derivative_visualizations_permitted",
            "approved_for_public_build",
        ):
            if not isinstance(raw_decision[field], bool):
                raise ValueError(f"The {field} decision for {source_id!r} must be Boolean.")


def assert_publication_allowed(
    config: Mapping[str, Any], source_id: str, *, derivative: bool = False
) -> Mapping[str, Any]:
    """Return an approved source decision or fail closed."""
    validate_source_registry(config)
    sources: Mapping[str, Any] = config["sources"]
    if source_id not in sources:
        raise ValueError(f"Source {source_id!r} is not in the rights registry.")
    decision: Mapping[str, Any] = sources[source_id]
    permitted = bool(decision["redistribution_permitted"])
    if derivative:
        permitted = permitted and bool(decision["derivative_visualizations_permitted"])
    if not decision["approved_for_public_build"] or not permitted:
        raise PermissionError(f"Source {source_id!r} is excluded from the public build.")
    return decision


def approved_source_ids(config: Mapping[str, Any]) -> list[str]:
    """List sources that pass the complete public-build decision."""
    validate_source_registry(config)
    sources: Mapping[str, Mapping[str, Any]] = config["sources"]
    return [
        source_id
        for source_id, decision in sources.items()
        if decision["approved_for_public_build"]
        and decision["redistribution_permitted"]
        and decision["derivative_visualizations_permitted"]
    ]
