from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["svg.hashsalt"] = "sc-education-finance-analysis"

BLUE = "#0072B2"
ORANGE = "#E69F00"
GRAY = "#8A8A8A"


def _finish(figure: plt.Figure, output: Path, caption: str) -> None:
    figure.text(0.01, 0.01, caption, fontsize=8, color="#444444")
    svg_path = output.with_suffix(".svg")
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "sc-education-finance"},
    )
    clean_svg = "\n".join(line.rstrip() for line in svg_path.read_text().splitlines())
    with svg_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(clean_svg + "\n")
    figure.savefig(
        output.with_suffix(".png"),
        dpi=300,
        bbox_inches="tight",
        metadata={"Software": "sc-education-finance"},
    )
    plt.close(figure)


def rpp_trends(frame: pd.DataFrame, output: Path, *, start_year: int) -> None:
    data = frame[
        (frame["metric"] == "regional_price_parity_all_items")
        & (frame["year"] >= start_year)
    ].copy()
    figure, axis = plt.subplots(figsize=(11, 7))
    endpoints: list[tuple[str, int, float, str]] = []
    for state, group in data.groupby("geography", sort=True):
        group = group.sort_values("year")
        highlight = state == "South Carolina"
        color = BLUE if highlight else GRAY
        axis.plot(
            group["year"],
            group["value"],
            color=color,
            alpha=1.0 if highlight else 0.45,
            linewidth=3.0 if highlight else 1.2,
        )
        last = group.iloc[-1]
        endpoints.append((str(state), int(last["year"]), float(last["value"]), color))

    positions: dict[str, float] = {}
    prior = -float("inf")
    for state, _, value, _ in sorted(endpoints, key=lambda item: item[2]):
        positions[state] = max(value, prior + 0.55)
        prior = positions[state]
    overflow = max(positions.values()) - (float(data["value"].max()) + 2.5)
    if overflow > 0:
        positions = {state: value - overflow for state, value in positions.items()}

    for state, year, value, color in endpoints:
        axis.annotate(
            state,
            xy=(year, value),
            xytext=(year + 0.35, positions[state]),
            color=color,
            fontsize=7.5,
            va="center",
            arrowprops={"arrowstyle": "-", "color": color, "alpha": 0.55},
            annotation_clip=False,
        )
    axis.axhline(100, color=ORANGE, linestyle="--", linewidth=1.2)
    axis.text(start_year, 100.25, "U.S. price level = 100", color="#8A6400", fontsize=8)
    axis.set_title(
        "Regional price parity trends across Southeastern peer states",
        loc="left",
        fontsize=16,
        fontweight="bold",
    )
    axis.set_ylabel("Regional price parity index")
    axis.set_xlabel("Year")
    axis.grid(axis="y", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.margins(x=0.15)
    _finish(
        figure,
        output,
        "Source: U.S. Bureau of Economic Analysis. Values below 100 indicate prices below the national level.",
    )


def sc_peer_comparison(frame: pd.DataFrame, output: Path, *, year: int) -> None:
    data = frame[
        (frame["metric"] == "regional_price_parity_all_items") & (frame["year"] == year)
    ].sort_values("value")
    colors = [BLUE if state == "South Carolina" else GRAY for state in data["geography"]]
    figure, axis = plt.subplots(figsize=(10, 7))
    bars = axis.barh(data["geography"], data["value"], color=colors)
    axis.bar_label(
        bars,
        labels=[f"{value:.3f}" for value in data["value"]],
        padding=4,
        fontsize=8,
    )
    axis.axvline(100, color=ORANGE, linestyle="--", linewidth=1.2)
    axis.set_title(
        f"South Carolina regional prices within its peer group, {year}",
        loc="left",
        fontsize=16,
        fontweight="bold",
    )
    axis.set_xlabel("Regional price parity index (United States = 100)")
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.margins(x=0.12)
    _finish(
        figure,
        output,
        "Source: U.S. Bureau of Economic Analysis. South Carolina is highlighted.",
    )


def render_all(frame: pd.DataFrame, output: Path, *, start_year: int, latest_year: int) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rpp_trends(frame, output / "southeastern-rpp-trends", start_year=start_year)
    sc_peer_comparison(frame, output / "south-carolina-peer-rpp", year=latest_year)
