from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

plt.rcParams["svg.hashsalt"] = "sc-education-finance-analysis"

BLUE = "#0072B2"
ORANGE = "#E69F00"
GRAY = "#8A8A8A"
GREEN = "#009E73"


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


def salary_trends(
    frame: pd.DataFrame, output: Path, *, latest_regional_actual_year: int
) -> None:
    data = frame[
        (frame["metric"] == "average_teacher_salary")
        & (frame["geography"].isin(["South Carolina", "Southeastern average"]))
    ].copy()
    figure, axis = plt.subplots(figsize=(11, 7))
    colors = {"South Carolina": BLUE, "Southeastern average": ORANGE}
    for geography in ("South Carolina", "Southeastern average"):
        group = data[data["geography"] == geography].sort_values("year")
        actual = group[group["status"] == "actual"]
        axis.plot(
            actual["year"],
            actual["value"],
            color=colors[geography],
            linewidth=2.6,
            marker="o",
        )
        estimates = group[group["status"] == "estimated"]
        if not estimates.empty:
            bridge = pd.concat([actual.tail(1), estimates])
            axis.plot(
                bridge["year"],
                bridge["value"],
                color=colors[geography],
                linewidth=2.6,
                linestyle="--",
                marker="o",
            )
        last = group.iloc[-1]
        label = geography
        if geography == "Southeastern average":
            label += " (estimated after FY 2023-24)"
        axis.annotate(
            f"{label}  ${float(last['value']):,.0f}",
            (int(last["year"]), float(last["value"])),
            xytext=(8, 0),
            textcoords="offset points",
            color=colors[geography],
            va="center",
            fontsize=9,
            annotation_clip=False,
        )
    axis.axvline(latest_regional_actual_year, color="#CCCCCC", linewidth=1)
    axis.text(
        latest_regional_actual_year + 0.08,
        float(data["value"].min()),
        "RFA regional estimates begin after FY 2023-24",
        color="#666666",
        fontsize=8,
        rotation=90,
        va="bottom",
    )
    axis.set_title(
        "South Carolina teacher salary and the Southeastern average",
        loc="left",
        fontsize=16,
        fontweight="bold",
    )
    axis.set_xlabel("Fiscal year ending")
    axis.set_ylabel("Average teacher salary")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
    axis.grid(axis="y", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.margins(x=0.18)
    _finish(
        figure,
        output,
        "Source: S.C. Revenue and Fiscal Affairs Office, FY 2026-27 survey. Dashed values are estimates.",
    )


def peer_salary_estimates(frame: pd.DataFrame, output: Path) -> None:
    data = frame.sort_values(["geography", "year"])
    figure, axis = plt.subplots(figsize=(11, 8))
    endpoints: list[tuple[str, float]] = []
    for state, group in data.groupby("geography", sort=True):
        color = BLUE if state in {"Virginia", "Mississippi"} else GRAY
        axis.plot(
            group["year"],
            group["nominal_salary"],
            color=color,
            linestyle="--",
            linewidth=2 if color == BLUE else 1.2,
            marker="o",
            alpha=1 if color == BLUE else 0.7,
        )
        revised = group[group["is_revised"].astype(bool)]
        for year, value in revised[["year", "nominal_salary"]].itertuples(
            index=False, name=None
        ):
            axis.annotate(
                "r",
                (int(str(year)), float(str(value))),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                color="#555555",
            )
        last = group.iloc[-1]
        endpoints.append((str(state), float(last["nominal_salary"])))

    positions: dict[str, float] = {}
    prior = -float("inf")
    for state, value in sorted(endpoints, key=lambda item: item[1]):
        positions[state] = max(value, prior + 1_150)
        prior = positions[state]
    overflow = max(positions.values()) - (float(data["nominal_salary"].max()) + 4_000)
    if overflow > 0:
        positions = {state: value - overflow for state, value in positions.items()}
    for state, value in endpoints:
        color = BLUE if state in {"Virginia", "Mississippi"} else "#555555"
        axis.annotate(
            f"{state}  ${value:,.0f}",
            xy=(2027, value),
            xytext=(2027.08, positions[state]),
            color=color,
            va="center",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "color": color, "alpha": 0.5},
            annotation_clip=False,
        )
    axis.set_xticks([2026, 2027], ["FY 2025-26", "FY 2026-27"])
    axis.set_xlim(2025.9, 2027.55)
    axis.set_title(
        "Southeastern teacher salary estimates",
        loc="left",
        fontsize=16,
        fontweight="bold",
    )
    axis.set_ylabel("Average teacher salary")
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
    axis.grid(axis="y", alpha=0.2)
    axis.spines[["top", "right"]].set_visible(False)
    _finish(
        figure,
        output,
        "Source: S.C. Revenue and Fiscal Affairs Office, FY 2026-27 survey. All values are estimates; r means revised.",
    )


def adjusted_salary_comparison(frame: pd.DataFrame, output: Path, *, rpp_year: int) -> None:
    latest_year = int(frame["year"].max())
    data = frame[frame["year"] == latest_year].sort_values("purchasing_power_salary")
    colors = [GREEN if state == "Georgia" else GRAY for state in data["geography"]]
    figure, axis = plt.subplots(figsize=(10, 7.5))
    bars = axis.barh(data["geography"], data["purchasing_power_salary"], color=colors)
    axis.bar_label(
        bars,
        labels=[f"${value:,.0f}" for value in data["purchasing_power_salary"]],
        padding=4,
        fontsize=8,
    )
    axis.set_title(
        "Estimated teacher salaries after regional price adjustment, FY 2026-27",
        loc="left",
        fontsize=15,
        fontweight="bold",
    )
    axis.set_xlabel(f"Salary in purchasing-power dollars using {rpp_year} regional prices")
    axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
    axis.grid(axis="x", alpha=0.2)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.margins(x=0.14)
    _finish(
        figure,
        output,
        "Sources: S.C. Revenue and Fiscal Affairs Office salary estimates and U.S. Bureau of Economic Analysis 2024 RPP. The RPP year precedes the salary estimate.",
    )


def render_all(
    frame: pd.DataFrame,
    salary_comparison: pd.DataFrame,
    output: Path,
    *,
    start_year: int,
    latest_year: int,
    salary_latest_regional_actual_year: int,
    salary_rpp_year: int,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rpp_trends(frame, output / "southeastern-rpp-trends", start_year=start_year)
    sc_peer_comparison(frame, output / "south-carolina-peer-rpp", year=latest_year)
    salary_trends(
        frame,
        output / "salary-trends",
        latest_regional_actual_year=salary_latest_regional_actual_year,
    )
    peer_salary_estimates(salary_comparison, output / "peer-salary-estimates")
    adjusted_salary_comparison(
        salary_comparison,
        output / "adjusted-salary-comparison",
        rpp_year=salary_rpp_year,
    )
