from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.extract import (
    _rfa_cells,
    extract_rfa_salary_pdf,
    load_rfa_salary_snapshot,
)

ROOT = Path(__file__).parents[1]
SNAPSHOT = ROOT / "data/source/rfa-teacher-salary-selected.csv"
PEERS = {
    "Alabama",
    "Arkansas",
    "Florida",
    "Georgia",
    "Kentucky",
    "Louisiana",
    "Mississippi",
    "North Carolina",
    "Tennessee",
    "Virginia",
    "West Virginia",
}


def test_rfa_row_parser_preserves_revision_markers() -> None:
    assert _rfa_cells("Zone Alpha 50,000 r 51,250") == [
        (50_000.0, True),
        (51_250.0, False),
    ]


def test_rfa_pdf_layout_change_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("sc_education_finance.extract.read_pdf_text", lambda _: "unexpected")
    with pytest.raises(ValueError, match="layout changed"):
        extract_rfa_salary_pdf(
            tmp_path / "invented.pdf",
            source_release="test",
            peer_states=PEERS,
        )


def test_selected_snapshot_preserves_estimates_and_revisions() -> None:
    records = load_rfa_salary_snapshot(
        SNAPSHOT,
        source_release="2025-11-19",
        peer_states=PEERS,
    )
    kentucky_2026 = next(
        record for record in records if record.geography == "Kentucky" and record.year == 2026
    )
    alabama_2027 = next(
        record for record in records if record.geography == "Alabama" and record.year == 2027
    )
    assert kentucky_2026.status == "estimated"
    assert kentucky_2026.is_revised is True
    assert alabama_2027.status == "estimated"
    assert alabama_2027.is_revised is False


def test_selected_snapshot_rejects_incomplete_coverage(tmp_path: Path) -> None:
    frame = pd.read_csv(SNAPSHOT)
    frame = frame[
        ~((frame["geography"] == "Alabama") & (frame["year"] == 2027))
    ]
    incomplete = tmp_path / "incomplete.csv"
    frame.to_csv(incomplete, index=False)
    with pytest.raises(ValueError, match="coverage changed"):
        load_rfa_salary_snapshot(
            incomplete,
            source_release="2025-11-19",
            peer_states=PEERS,
        )


def test_selected_snapshot_rejects_duplicates(tmp_path: Path) -> None:
    frame = pd.read_csv(SNAPSHOT)
    duplicate = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    path = tmp_path / "duplicate.csv"
    duplicate.to_csv(path, index=False)
    with pytest.raises(ValueError, match="Duplicate"):
        load_rfa_salary_snapshot(
            path,
            source_release="2025-11-19",
            peer_states=PEERS,
        )
