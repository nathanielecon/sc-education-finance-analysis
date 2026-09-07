from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

plt.rcParams["svg.hashsalt"] = "sc-education-finance-analysis"

BLUE = "#0072B2"
ORANGE = "#E69F00"
GRAY = "#8A8A8A"
LIGHT_BLUE = "#DCEFF8"


def _finish(figure: plt.Figure, output: Path, caption: str) -> None:
    figure.text(0.01, 0.01, caption, fontsize=8, color="#444444")
    svg_path = output.with_suffix(".svg")
    figure.savefig(
        svg_path,
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "sc-education-finance"},
    )
    clean_svg = "\n".join(
        line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()
    )
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
        "Regional Price Parity Trends Across Southeastern Peer States",
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
        f"South Carolina Regional Prices Within Its Peer Group, {year}",
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
        if geography == "South Carolina" and not actual.empty:
            current = actual.iloc[-1]
            axis.annotate(
                f"${float(current['value']):,.0f} Actual",
                (int(current["year"]), float(current["value"])),
                xytext=(-8, 10),
                textcoords="offset points",
                color=colors[geography],
                ha="right",
                va="bottom",
                fontsize=7.5,
            )
        estimates = group[group["status"] == "estimated"]
        if not estimates.empty:
            bridge = pd.concat([actual.tail(1), estimates])
            axis.plot(
                bridge["year"],
                bridge["value"],
                color=colors[geography],
                linewidth=2.6,
                linestyle=":" if geography == "South Carolina" else "--",
                marker="o",
            )
        scenarios = group[group["status"] == "modeled_scenario"]
        if not scenarios.empty:
            bridge_start = estimates.tail(1) if not estimates.empty else actual.tail(1)
            bridge = pd.concat([bridge_start, scenarios])
            axis.plot(
                bridge["year"],
                bridge["value"],
                color=colors[geography],
                linewidth=2.6,
                linestyle=":",
                marker="o",
                markerfacecolor="white",
                markeredgewidth=2,
            )
        for point in group[group["status"] != "actual"].itertuples():
            label = "Estimate" if point.status == "estimated" else "Schedule-Only Scenario"
            y_offset = 10 if geography == "South Carolina" else -14
            axis.annotate(
                f"${float(cast(Any, point.value)):,.0f} {label}",
                (int(cast(Any, point.year)), float(cast(Any, point.value))),
                xytext=(0, y_offset),
                textcoords="offset points",
                color=colors[geography],
                ha="center",
                va="bottom" if y_offset > 0 else "top",
                fontsize=7.5,
            )
        last = group.iloc[-1]
        axis.annotate(
            geography,
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
        "South Carolina Teacher Salary and the Southeastern Average",
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
        "Sources: S.C. Revenue and Fiscal Affairs Office; National Education Association, table E-6; South Carolina FY 2026-27 budget and final salary schedule. Dotted South Carolina values are an estimate and a schedule-only scenario. Dashed regional values are RFA estimates.",
    )


def salary_comparison_side_by_side(
    frame: pd.DataFrame, output: Path, *, rpp_year: int
) -> None:
    year = int(cast(Any, frame["year"].iloc[0]))
    data = frame.sort_values("nominal_salary", ascending=False).reset_index(drop=True)
    colors = [BLUE if state == "South Carolina" else GRAY for state in data["geography"]]
    figure, axes = plt.subplots(1, 2, figsize=(15, 8.5), sharey=True)
    scale_max = 1.18 * max(
        float(data["nominal_salary"].max()),
        float(data["purchasing_power_salary"].max()),
    )
    panels = (
        (axes[0], "nominal_salary", "Nominal Salary", "nominal_rank"),
        (
            axes[1],
            "purchasing_power_salary",
            f"Salary Adjusted With {rpp_year} RPP",
            "purchasing_power_rank",
        ),
    )
    sc_index = int(cast(Any, data.index[data["geography"] == "South Carolina"].item()))
    for axis, column, title, rank_column in panels:
        axis.axhspan(sc_index - 0.5, sc_index + 0.5, color=LIGHT_BLUE, zorder=0)
        bars = axis.barh(data["geography"], data[column], color=colors, zorder=2)
        labels = [f"${value:,.0f}" for value in data[column]]
        sc_rank = int(cast(Any, data.loc[sc_index, rank_column]))
        labels[sc_index] += f"  #{sc_rank}" + (" · Top 5" if rank_column == "nominal_rank" else "")
        axis.bar_label(bars, labels=labels, padding=4, fontsize=8)
        axis.set_title(title, fontsize=13, fontweight="bold")
        axis.set_xlim(0, scale_max)
        axis.set_xlabel("Annual Salary")
        axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:,.0f}"))
        axis.grid(axis="x", alpha=0.2, zorder=1)
        axis.spines[["top", "right", "left"]].set_visible(False)
    axes[0].invert_yaxis()
    figure.suptitle(
        f"Teacher Salaries Before and After Regional Price Adjustment, FY {year - 1}-{str(year)[-2:]}",
        x=0.06,
        ha="left",
        fontsize=16,
        fontweight="bold",
    )
    _finish(
        figure,
        output,
        "Sources: S.C. Revenue and Fiscal Affairs Office FY 2026-27 survey and U.S. Bureau of Economic Analysis 2024 RPP. South Carolina is lightly shaded. RFA reports South Carolina as actual and marks peer-state values as revised estimates.",
    )


def naep_heatmap(frame: pd.DataFrame, output: Path) -> None:
    metric_order = [
        "naep_grade_4_mathematics_at_or_above_proficient",
        "naep_grade_4_reading_at_or_above_proficient",
        "naep_grade_8_mathematics_at_or_above_proficient",
        "naep_grade_8_reading_at_or_above_proficient",
    ]
    labels = ["Grade 4\nMathematics", "Grade 4\nReading", "Grade 8\nMathematics", "Grade 8\nReading"]
    states = sorted(frame["geography"].unique())
    values = frame.pivot(index="geography", columns="metric", values="value").loc[
        states, metric_order
    ]
    ranks = frame.pivot(index="geography", columns="metric", values="regional_rank").loc[
        states, metric_order
    ]
    figure, axis = plt.subplots(figsize=(10.5, 8.5))
    image = axis.imshow(values.to_numpy(), cmap="viridis", aspect="auto", vmin=15, vmax=50)
    axis.set_xticks(range(len(labels)), labels=labels)
    axis.set_yticks(range(len(states)), labels=states)
    axis.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)
    sc_index = states.index("South Carolina")
    axis.axhspan(sc_index - 0.49, sc_index + 0.49, facecolor="none", edgecolor=BLUE, linewidth=3)
    for row_index, state in enumerate(states):
        for column_index, value in enumerate(values.loc[state]):
            text = f"{value:.1f}%"
            if state == "South Carolina":
                text += f"\n#{int(cast(Any, ranks.iloc[row_index, column_index]))}"
            color = "white" if value < 32 or value > 43 else "black"
            axis.text(
                column_index,
                row_index,
                text,
                ha="center",
                va="center",
                color=color,
                fontsize=8.5,
                fontweight="bold" if state == "South Carolina" else "normal",
            )
    axis.set_title(
        "NAEP Mathematics and Reading Results Across Southeastern States, 2024",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=42,
    )
    colorbar = figure.colorbar(image, ax=axis, fraction=0.035, pad=0.04)
    colorbar.set_label("Percent At or Above NAEP Proficient")
    _finish(
        figure,
        output,
        "Source: National Center for Education Statistics, 2024 NAEP Data Service. Public-school students. South Carolina is outlined, and its cells show regional point-estimate ranks. NAEP Proficient is not the same as grade-level proficiency. Differences may not be statistically significant.",
    )


def render_all(
    frame: pd.DataFrame,
    salary_comparison: pd.DataFrame,
    naep_comparison: pd.DataFrame,
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
    salary_comparison_side_by_side(
        salary_comparison,
        output / "salary-comparison-side-by-side",
        rpp_year=salary_rpp_year,
    )
    naep_heatmap(naep_comparison, output / "naep-regional-comparison")
