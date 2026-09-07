from pathlib import Path

import pandas as pd
import pytest

from sc_education_finance.charts import salary_trends
from sc_education_finance.extract import (
    SCENARIO_METHOD,
    derive_south_carolina_salary_scenario,
    load_selected_records,
)
from sc_education_finance.pipeline import (
    assert_salary_table_rankable,
    select_latest_salary_rows,
)
from sc_education_finance.records import Record

ROOT = Path(__file__).parents[1]


def _inputs() -> list[Record]:
    return [
        *load_selected_records(ROOT / "data/source/nea-south-carolina-salary-selected.csv"),
        *load_selected_records(
            ROOT / "data/source/sc-teacher-schedule-increase-selected.csv"
        ),
    ]


def test_scenario_is_calculated_from_approved_inputs() -> None:
    inputs = _inputs()
    scenario = derive_south_carolina_salary_scenario(inputs)
    assert [record.value for record in inputs] == [67_107, 2_000]
    assert scenario.value == 69_107
    assert scenario.status == "modeled_scenario"
    assert scenario.method == SCENARIO_METHOD
    assert scenario.input_source_ids
    assert scenario.assumptions


@pytest.mark.parametrize(("input_index", "increase"), [(0, 100), (1, 250)])
def test_scenario_changes_when_an_input_changes(input_index: int, increase: int) -> None:
    inputs = _inputs()
    selected = inputs[input_index]
    inputs[input_index] = Record(
        **{**selected.as_dict(), "value": selected.value + increase}
    )
    assert derive_south_carolina_salary_scenario(inputs).value == 69_107 + increase


def test_scenario_input_change_updates_generated_figure(tmp_path: Path) -> None:
    frame = pd.read_csv(ROOT / "data/curated/observations.csv")
    salary = frame[
        (frame["metric"] == "average_teacher_salary")
        & (frame["geography"].isin(["South Carolina", "Southeastern average"]))
    ].copy()
    inputs = _inputs()
    inputs[1] = Record(**{**inputs[1].as_dict(), "value": 2_250})
    changed = derive_south_carolina_salary_scenario(inputs)
    scenario_mask = (
        (salary["geography"] == "South Carolina")
        & (salary["status"] == "modeled_scenario")
    )
    salary.loc[scenario_mask, "value"] = changed.value

    salary_trends(salary, tmp_path / "salary-trends", latest_regional_actual_year=2024)
    svg = (tmp_path / "salary-trends.svg").read_text(encoding="utf-8")
    assert "$69,357 Schedule-Only Scenario" in svg
    assert "$69,107 Schedule-Only Scenario" not in svg


def test_latest_table_prefers_an_actual_over_later_estimates() -> None:
    frame = pd.read_csv(ROOT / "data/curated/observations.csv")
    selected = select_latest_salary_rows(frame, {"South Carolina", "Virginia"})
    south_carolina = selected[selected["geography"] == "South Carolina"].iloc[0]
    virginia = selected[selected["geography"] == "Virginia"].iloc[0]
    assert south_carolina["year"] == 2025
    assert south_carolina["status"] == "actual"
    assert virginia["year"] == 2027
    assert virginia["status"] == "estimated"


def test_mixed_vintage_salary_table_cannot_be_ranked() -> None:
    frame = pd.read_csv(ROOT / "data/curated/latest-available-teacher-salaries.csv")
    with pytest.raises(ValueError, match="cannot be ranked"):
        assert_salary_table_rankable(frame)


def test_public_prose_labels_estimate_and_scenario_correctly() -> None:
    text = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs/findings.md").read_text(encoding="utf-8"),
        ]
    )
    assert "$67,107" in text and "estimate" in text.lower()
    assert "$69,107" in text and "schedule-only scenario" in text.lower()
    assert "$69,107 official projection" not in text.lower()
