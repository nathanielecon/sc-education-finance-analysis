from typing import Any

import pytest

from sc_education_finance.rights import (
    approved_source_ids,
    assert_source_use_allowed,
    validate_source_registry,
)


def decision(*, approved: bool) -> dict[str, Any]:
    return {
        "publisher": "Synthetic Publisher",
        "landing_url": "https://example.test/data",
        "rights_basis": "Invented test decision.",
        "rights_url": "https://example.test/rights",
        "download_permitted": approved,
        "factual_extraction_permitted": approved,
        "raw_redistribution_permitted": approved,
        "derivative_visualizations_permitted": approved,
        "approved_for_public_build": approved,
        "reviewed_on": "2026-09-07",
    }


def test_only_fully_approved_source_is_public() -> None:
    config = {"sources": {"approved": decision(approved=True), "blocked": decision(approved=False)}}
    assert approved_source_ids(config, use="factual_extraction") == ["approved"]
    assert (
        assert_source_use_allowed(config, "approved", use="factual_extraction")["publisher"]
        == "Synthetic Publisher"
    )
    with pytest.raises(PermissionError, match="does not permit"):
        assert_source_use_allowed(config, "blocked", use="derivative_visualization")


def test_unregistered_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="not in the rights registry"):
        assert_source_use_allowed(
            {"sources": {"approved": decision(approved=True)}},
            "unknown",
            use="download",
        )


def test_missing_rights_url_fails_closed() -> None:
    incomplete = decision(approved=True)
    del incomplete["rights_url"]
    with pytest.raises(ValueError, match="missing"):
        validate_source_registry({"sources": {"incomplete": incomplete}})


def test_source_can_allow_facts_without_raw_redistribution() -> None:
    limited = decision(approved=True)
    limited["raw_redistribution_permitted"] = False
    config = {"sources": {"limited": limited}}
    assert approved_source_ids(config, use="factual_extraction") == ["limited"]
    assert approved_source_ids(config, use="raw_redistribution") == []
    with pytest.raises(PermissionError, match="raw_redistribution"):
        assert_source_use_allowed(config, "limited", use="raw_redistribution")
