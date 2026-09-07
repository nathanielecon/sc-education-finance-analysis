import pytest

from sc_education_finance.metrics import (
    competition_ranks,
    normalize_state,
    percentage_change,
    purchasing_power,
    weighted_average,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("North", "North Carolina"),
        ("N. Carolina", "North Carolina"),
        ("South", "South Carolina"),
        ("West", "West Virginia"),
        ("W. Virginia", "West Virginia"),
    ],
)
def test_normalize_state(raw: str, expected: str) -> None:
    assert normalize_state(raw) == expected


def test_percentage_change_uses_old_value_as_denominator() -> None:
    assert percentage_change(100, 125) == pytest.approx(25)


def test_rpp_adjustment() -> None:
    assert purchasing_power(67_107, 98.284) == pytest.approx(68_278.6618)


def test_weighted_average() -> None:
    assert weighted_average([(50, 2), (80, 1)]) == pytest.approx(60)


def test_competition_ranks_preserve_ties() -> None:
    assert competition_ranks([20, 10, 20, 5]) == [1, 3, 1, 4]


def test_invalid_denominators_fail() -> None:
    with pytest.raises(ValueError):
        percentage_change(0, 1)
    with pytest.raises(ValueError):
        purchasing_power(1, 0)
