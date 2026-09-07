from __future__ import annotations

from collections.abc import Iterable

STATE_ALIASES = {
    "North": "North Carolina",
    "N. Carolina": "North Carolina",
    "South": "South Carolina",
    "S. Carolina": "South Carolina",
    "West": "West Virginia",
    "W. Virginia": "West Virginia",
}


def normalize_state(value: str) -> str:
    """Expand historical state labels and trim whitespace."""
    clean = " ".join(value.split())
    return STATE_ALIASES.get(clean, clean)


def percentage_change(old: float, new: float) -> float:
    """Return the percentage change from old to new."""
    if old == 0:
        raise ValueError("The old value cannot be zero.")
    return (new - old) / old * 100


def purchasing_power(nominal: float, rpp: float) -> float:
    """Adjust a nominal amount with a regional price parity index."""
    if rpp <= 0:
        raise ValueError("RPP must be positive.")
    return nominal / (rpp / 100)


def weighted_average(values: Iterable[tuple[float, float]]) -> float:
    """Calculate an average weighted by teacher count."""
    pairs = list(values)
    weight = sum(item[1] for item in pairs)
    if weight <= 0:
        raise ValueError("Total weight must be positive.")
    return sum(value * item_weight for value, item_weight in pairs) / weight


def competition_ranks(values: Iterable[float], *, descending: bool = True) -> list[int]:
    """Return competition ranks and preserve ties."""
    items = list(values)
    ordered = sorted(set(items), reverse=descending)
    rank_map = {value: 1 + sum(candidate > value for candidate in items) for value in ordered}
    if not descending:
        rank_map = {value: 1 + sum(candidate < value for candidate in items) for value in ordered}
    return [rank_map[value] for value in items]
