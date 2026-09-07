from typing import Any

import pytest

from sc_education_finance.rights import (
    approved_source_ids,
    assert_publication_allowed,
    validate_source_registry,
)


def decision(*, approved: bool) -> dict[str, Any]:
    return {
        "publisher": "Synthetic Publisher",
        "landing_url": "https://example.test/data",
        "rights_basis": "Invented test decision.",
        "rights_url": "https://example.test/rights",
        "redistribution_permitted": approved,
        "derivative_visualizations_permitted": approved,
        "approved_for_public_build": approved,
        "reviewed_on": "2026-09-07",
    }


def test_only_fully_approved_source_is_public() -> None:
    config = {"sources": {"approved": decision(approved=True), "blocked": decision(approved=False)}}
    assert approved_source_ids(config) == ["approved"]
    assert assert_publication_allowed(config, "approved")["publisher"] == "Synthetic Publisher"
    with pytest.raises(PermissionError, match="excluded"):
        assert_publication_allowed(config, "blocked", derivative=True)


def test_unregistered_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="not in the rights registry"):
        assert_publication_allowed({"sources": {"approved": decision(approved=True)}}, "unknown")


def test_missing_rights_url_fails_closed() -> None:
    incomplete = decision(approved=True)
    del incomplete["rights_url"]
    with pytest.raises(ValueError, match="missing"):
        validate_source_registry({"sources": {"incomplete": incomplete}})
